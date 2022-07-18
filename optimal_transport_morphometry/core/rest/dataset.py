from typing import List

from django.contrib.auth.models import User
from django.db.models import Q
from drf_yasg.utils import swagger_auto_schema
from guardian.shortcuts import assign_perm, get_objects_for_user, get_users_with_perms
from rest_framework import serializers, status
from rest_framework.decorators import action
from rest_framework.exceptions import NotAuthenticated, PermissionDenied
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import SAFE_METHODS, BasePermission
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from optimal_transport_morphometry.core.models import Dataset, Image
from optimal_transport_morphometry.core.rest.feature_image import FeatureImageSerializer
from optimal_transport_morphometry.core.rest.image import ImageSerializer
from optimal_transport_morphometry.core.rest.jacobian_image import JacobianImageSerializer
from optimal_transport_morphometry.core.rest.registered_image import RegisteredImageSerializer
from optimal_transport_morphometry.core.rest.segmented_image import SegmentedImageSerializer
from optimal_transport_morphometry.core.rest.user import UserSerializer


class DatasetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dataset
        fields = [
            'id',
            'name',
            'description',
            'public',
            'preprocessing_complete',
            'analysis_complete',
        ]
        read_only_fields = ['id', 'preprocessing_complete', 'analysis_complete']

    # Set default value
    public = serializers.BooleanField(default=False)


class DatasetDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dataset
        fields = [
            'id',
            'name',
            'description',
            'public',
            'preprocessing_complete',
            'analysis_complete',
            'write_access',
        ]
        read_only_fields = fields

    # Add extra fields
    write_access = serializers.BooleanField(required=False, read_only=True)


class DatasetListQuerySerializer(serializers.Serializer):
    # Add fields for filtering
    name = serializers.CharField(required=False)
    public = serializers.BooleanField(required=False, default=True)
    owner = serializers.BooleanField(required=False, default=True)
    shared = serializers.BooleanField(required=False, default=True)


class ImageGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Image
        new_fields = ['registered', 'jacobian', 'segmented', 'feature']
        fields = ImageSerializer.Meta.fields + new_fields
        read_only_fields = ImageSerializer.Meta.fields + new_fields

    registered = serializers.SerializerMethodField()
    jacobian = serializers.SerializerMethodField()
    segmented = serializers.SerializerMethodField()
    feature = serializers.SerializerMethodField()

    def get_registered(self, obj: Image):
        im = obj.registered_images.first()
        if im is None:
            return None

        return RegisteredImageSerializer(im).data

    def get_jacobian(self, obj: Image):
        im = obj.jacobian_images.first()
        if im is None:
            return None

        return JacobianImageSerializer(im).data

    def get_segmented(self, obj: Image):
        im = obj.segmented_images.first()
        if im is None:
            return None

        return SegmentedImageSerializer(im).data

    def get_feature(self, obj: Image):
        im = obj.feature_images.first()
        if im is None:
            return None

        return FeatureImageSerializer(im).data


class CreateBatchSerializer(serializers.Serializer):
    csvfile = serializers.FileField(allow_empty_file=False, max_length=1024 * 1024)


class DatasetCollaboratorSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id',
            'username',
        ]

    # Redeclare username to remove error for exsting users
    username = serializers.CharField()


class DatasetPermissions(BasePermission):
    def has_permission(self, request: Request, view):
        # Any user can list or create datasets
        return True

    def has_object_permission(self, request: Request, view, dataset: Dataset):
        if dataset.public and request.method in SAFE_METHODS:
            return True

        user: User = request.user
        if not user.is_authenticated:
            raise NotAuthenticated()

        if not dataset.has_write_access(user):
            raise PermissionDenied()

        # Nothing wrong, permission allowed
        return True


class DatasetViewSet(ModelViewSet):
    queryset = Dataset.objects.select_related('owner').all()

    permission_classes = [DatasetPermissions]
    serializer_class = DatasetSerializer
    pagination_class = LimitOffsetPagination

    @swagger_auto_schema(
        operation_description='Retrieve a dataset by its ID.',
        responses={200: DatasetDetailSerializer()},
    )
    def retrieve(self, request, pk):
        dataset: Dataset = self.get_object()
        user: User = request.user

        # Add field to denote write access
        dataset.write_access = dataset.has_write_access(user)

        return Response(DatasetDetailSerializer(dataset).data)

    @swagger_auto_schema(
        operation_description='Create a new dataset.',
        query_serializer=DatasetListQuerySerializer(),
        responses={200: DatasetSerializer(many=True)},
    )
    def list(self, request, *args, **kwargs):
        # Serialize data
        serializer = DatasetListQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        # Build query
        model_filter = Q()
        user = request.user
        real_user = user.is_authenticated

        # Filter public
        if serializer.validated_data['public']:
            model_filter |= Q(public=True)

        # Filter public and owner
        if serializer.validated_data['owner'] and real_user:
            model_filter |= Q(owner=user)

        # Apply base filters
        queryset = self.queryset.none()
        if model_filter:
            queryset |= self.queryset.filter(model_filter)

        # Filter collaborator
        if serializer.validated_data['shared'] and real_user:
            queryset |= get_objects_for_user(user, 'collaborator', Dataset, with_superuser=False)

        # Filter name
        queryset = queryset.distinct()
        if 'name' in serializer.validated_data:
            queryset = queryset.filter(name__icontains=serializer.validated_data['name'])

        # Build response
        return self.get_paginated_response(
            DatasetSerializer(self.paginate_queryset(queryset), many=True).data
        )

    # TODO: Optimize this endpoint
    @action(detail=True, methods=['get'])
    def preprocessed_images(self, request, pk):
        dataset: Dataset = self.get_object()
        images = dataset.images.prefetch_related(
            'registered_images',
            'jacobian_images',
            'segmented_images',
            'feature_images',
        ).all()

        serializer = ImageGroupSerializer(images, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description='Create a new dataset.',
        request_body=DatasetSerializer(),
        responses={200: DatasetSerializer},
    )
    def create(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            raise serializers.ValidationError('Must be logged in to create a dataset')

        serializer: DatasetSerializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Dataset data
        name = serializer.validated_data['name']
        description = serializer.validated_data['description']
        public = serializer.validated_data['public']

        # Check that dataset doesn't already exist
        if Dataset.objects.filter(name=name, owner=request.user).exists():
            raise serializers.ValidationError(f'Dataset with name "{name}" already exists')

        # Perform create
        ds = Dataset.objects.create(
            name=name,
            description=description,
            public=public,
            owner=request.user,
        )
        return Response(DatasetSerializer(ds).data, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(
        operation_description='Set the collaborators of a dataset.',
        request_body=DatasetCollaboratorSerializer(many=True),
    )
    @action(detail=True, methods=['PUT'])
    def collaborators(self, request, pk: str):
        # Retrieve dataset, ensuring user is owner
        dataset: Dataset = self.get_object()
        if request.user != dataset.owner:
            raise PermissionDenied()

        # Validate input, raising errors if necessary
        serializer: DatasetCollaboratorSerializer = DatasetCollaboratorSerializer(
            data=request.data, many=True
        )
        serializer.is_valid(raise_exception=True)

        # Validate users
        users: List[User] = []
        for userdict in serializer.validated_data:
            username = userdict.get('username')
            user = User.objects.filter(username=username).first()
            if user is None:
                raise serializers.ValidationError(
                    {'username': f'User with username {username} not found.'}
                )

            # Check that user is not dataset owner
            if user == dataset.owner:
                raise serializers.ValidationError(
                    f"Cannot assign dataset owner '{user.username}' as collaborator."
                )

            users.append(user)

        # Assign perm to each user
        for user in users:
            assign_perm('collaborator', user, dataset)

        return Response(
            UserSerializer(
                get_users_with_perms(dataset, only_with_perms_in=['collaborator']), many=True
            ).data
        )

    @swagger_auto_schema(operation_description='Get the collaborators of a dataset.')
    @collaborators.mapping.get
    def get_collaborators(self, request, pk: str):
        if not request.user.is_authenticated:
            raise serializers.ValidationError('Must be logged in.')

        # Retrieve collaborators
        user: User = request.user
        dataset: Dataset = self.get_object()
        if not dataset.has_write_access(user):
            raise PermissionDenied('Must be owner or collaborator to view collaborators')

        # Return user list
        users = get_users_with_perms(dataset, only_with_perms_in=['collaborator'])
        return Response(UserSerializer(instance=users, many=True).data, status=status.HTTP_200_OK)
