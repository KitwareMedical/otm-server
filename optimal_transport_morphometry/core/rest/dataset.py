from typing import List

from django.contrib.auth.models import User
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django_filters import rest_framework as filters
from drf_yasg.utils import swagger_auto_schema
from guardian.shortcuts import assign_perm, get_objects_for_user, get_users_with_perms
from rest_framework import exceptions, serializers, status
from rest_framework.decorators import action
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
        write_access_allowed = user.is_authenticated and (
            user == dataset.owner or user.has_perm('collaborator', dataset)
        )
        if not write_access_allowed:
            # No need to worry about leaking that this dataset exists,
            # since the queryset filter will catch that before it gets here
            raise exceptions.PermissionDenied()

        # Nothing wrong, permission allowed
        return True


class DatasetViewSet(ModelViewSet):
    queryset = Dataset.objects.select_related('owner').all()

    permission_classes = [DatasetPermissions]
    serializer_class = DatasetSerializer

    filter_backends = [filters.DjangoFilterBackend]
    filterset_fields = ['name']

    def get_queryset(self):
        queryset = self.queryset
        user = self.request.user
        real_user = user.is_authenticated

        # Filter public and owner
        model_filter = Q(public=True)
        if real_user:
            model_filter |= Q(owner=user)

        # Filter collaborator
        queryset = queryset.filter(model_filter)
        if real_user:
            queryset |= get_objects_for_user(user, 'collaborator', Dataset, with_superuser=False)

        return queryset.distinct()

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
        if not request.user.is_authenticated:
            raise serializers.ValidationError('Must be logged in.')

        # Retrieve dataset, ensuring user is owner
        dataset: Dataset = get_object_or_404(Dataset.objects.select_related('owner'), id=pk)
        if request.user != dataset.owner:
            raise serializers.ValidationError('Only dataset owner can set collaborators.')

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

        return Response(None, status=status.HTTP_204_NO_CONTENT)

    @swagger_auto_schema(operation_description='Get the collaborators of a dataset.')
    @collaborators.mapping.get
    def get_collaborators(self, request, pk: str):
        if not request.user.is_authenticated:
            raise serializers.ValidationError('Must be logged in.')

        # Retrieve dataset and validate input, raising errors if necessary
        dataset: Dataset = get_object_or_404(Dataset.objects.select_related('owner'), id=pk)

        # Raise error if not owner or collaborator
        user: User = request.user
        if not (dataset.owner == request.user or user.has_perm('collaborator', dataset)):
            raise serializers.ValidationError('Must be owner or collaborator to view collaborators')

        # Retrieve collaborators
        users = get_users_with_perms(dataset, only_with_perms_in=['collaborator'])

        # Return user list
        return Response(UserSerializer(instance=users, many=True).data, status=status.HTTP_200_OK)
