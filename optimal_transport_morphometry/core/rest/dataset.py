import codecs
from typing import List

from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.db.models import Count, Exists, OuterRef
from django.shortcuts import get_object_or_404
from drf_yasg.utils import no_body, swagger_auto_schema
from guardian.shortcuts import assign_perm, get_objects_for_user, get_users_with_perms, remove_perm
from rest_framework import serializers, status
from rest_framework.decorators import action
from rest_framework.exceptions import NotAuthenticated, PermissionDenied
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import SAFE_METHODS, BasePermission
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from optimal_transport_morphometry.core.batch_parser import load_batch_from_csv
from optimal_transport_morphometry.core.models import (
    AnalysisResult,
    Atlas,
    Dataset,
    Image,
    PreprocessingBatch,
    UploadBatch,
)
from optimal_transport_morphometry.core.rest.analysis import AnalysisResultSerializer
from optimal_transport_morphometry.core.rest.image import ImageSerializer
from optimal_transport_morphometry.core.rest.preprocessing import PreprocessingBatchSerializer
from optimal_transport_morphometry.core.rest.serializers import LimitOffsetSerializer
from optimal_transport_morphometry.core.rest.upload_batch import UploadBatchSerializer
from optimal_transport_morphometry.core.rest.user import UserSerializer
from optimal_transport_morphometry.core.tasks import preprocess_images, run_utm


class DatasetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dataset
        fields = [
            'id',
            'name',
            'description',
            'public',
            'current_preprocessing_batch',
            'current_analysis_result',
        ]
        read_only_fields = [
            'id',
            'current_preprocessing_batch',
            'current_analysis_result',
        ]

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
            'current_preprocessing_batch',
            'current_analysis_result',
            # Extra
            'access',
            'uploads_active',
            'image_count',
        ]
        read_only_fields = fields

    # Add extra fields
    access = serializers.ChoiceField(
        required=False,
        read_only=True,
        choices=['admin', 'write', None],
    )

    uploads_active = serializers.BooleanField()
    image_count = serializers.IntegerField()
    current_preprocessing_batch = PreprocessingBatchSerializer()
    current_analysis_result = AnalysisResultSerializer()


class DatasetListQuerySerializer(serializers.Serializer):
    # Add fields for filtering
    name = serializers.CharField(required=False)
    access = serializers.ChoiceField(choices=['public', 'shared', 'owned'], required=False)


class CreateBatchSerializer(serializers.Serializer):
    csvfile = serializers.FileField(allow_empty_file=False, max_length=1024 * 1024)


class PreprocessResponseSerializer(serializers.Serializer):
    task_id = serializers.CharField()


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

        if dataset.user_access(user) is None:
            raise PermissionDenied()

        # Nothing wrong, permission allowed
        return True


class DatasetViewSet(ModelViewSet):
    queryset = Dataset.objects.select_related('owner', 'current_preprocessing_batch').all()

    permission_classes = [DatasetPermissions]
    serializer_class = DatasetSerializer
    pagination_class = LimitOffsetPagination

    def get_queryset(self):
        return Dataset.visible_datasets(self.request.user).select_related(
            'current_preprocessing_batch',
            'current_analysis_result',
        )

    @swagger_auto_schema(
        operation_description='Retrieve a dataset by its ID.',
        responses={200: DatasetDetailSerializer()},
    )
    def retrieve(self, request, pk):
        # Annotate image count and if uploads exist
        queryset = self.filter_queryset(self.get_queryset())
        queryset = queryset.annotate(
            image_count=Count('images', distinct=True),
            uploads_active=Exists(
                UploadBatch.objects.filter(dataset_id=OuterRef('id')),
            ),
        )

        # Retrieve dataset and check permissions
        dataset = get_object_or_404(queryset, id=pk)
        self.check_object_permissions(self.request, dataset)

        # Add field to denote write access
        dataset.access = dataset.user_access(request.user)

        # Return response
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

        # Retrieve values
        user: User = request.user
        access = serializer.validated_data.get('access')

        # Set queryset based on access param
        if access is None:
            # Return all accessible values if no access specified
            queryset = self.get_queryset()
        elif access == 'public' or not user.is_authenticated:
            queryset = self.queryset.filter(public=True)
        elif access == 'shared':
            queryset = get_objects_for_user(user, 'collaborator', Dataset, with_superuser=False)
        elif access == 'owned':
            queryset = Dataset.objects.filter(owner=user)
        else:
            raise Exception("Invalid state for serialized value 'access' achieved.")

        # Filter name
        name = serializer.validated_data.get('name')
        if name:
            queryset = queryset.filter(name__icontains=name)

        # Build response
        return self.get_paginated_response(
            DatasetSerializer(self.paginate_queryset(queryset), many=True).data
        )

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
        user: User = request.user
        if not user.is_authenticated:
            raise NotAuthenticated()

        # Get dataset
        dataset: Dataset = self.get_object()
        if user != dataset.owner:
            raise PermissionDenied()

        # Validate input, raising errors if necessary
        serializer: DatasetCollaboratorSerializer = DatasetCollaboratorSerializer(
            data=request.data, many=True
        )
        serializer.is_valid(raise_exception=True)

        # Check that dataset owner not added
        usernames = {userdict['username'] for userdict in serializer.validated_data}
        if dataset.owner.username in usernames:
            raise serializers.ValidationError(
                f"Cannot assign dataset owner '{dataset.owner.username}' as collaborator."
            )

        # Retrieve users, check if any not found
        users: List[User] = list(User.objects.filter(username__in=usernames))
        if len(users) != len(usernames):
            found = {user.username for user in users}
            not_found = [uname for uname in usernames if uname not in found]
            raise serializers.ValidationError(
                [
                    {'username': f'User with username {username} not found.'}
                    for username in not_found
                ]
            )

        # All users valid, add/remove as needed
        with transaction.atomic():
            # Remove existing users
            # TODO: Optimize this if possible
            for user in get_users_with_perms(dataset, only_with_perms_in=['collaborator']):
                remove_perm('collaborator', user, dataset)

            # Assign new users
            if users:
                assign_perm('collaborator', users, dataset)

        # Return response
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
        if dataset.user_access(user) is None:
            raise PermissionDenied('Must be owner or collaborator to view collaborators')

        # Return user list
        users = get_users_with_perms(dataset, only_with_perms_in=['collaborator'])
        return Response(UserSerializer(instance=users, many=True).data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description='Start preprocessing on a dataset.',
        request_body=no_body,
        responses={200: PreprocessingBatchSerializer()},
    )
    @action(detail=True, methods=['POST'])
    def preprocess(self, request, pk: str):
        dataset: Dataset = self.get_object()
        if (
            dataset.current_preprocessing_batch is not None
            and dataset.current_preprocessing_batch.status
            in [PreprocessingBatch.Status.PENDING, PreprocessingBatch.Status.RUNNING]
        ):
            raise serializers.ValidationError('Preprocessing currently running.')

        # Check against empty runs
        if not dataset.images.count():
            raise serializers.ValidationError('Cannot run preprocessing on empty dataset.')

        # Create new preprocessing batch
        batch = PreprocessingBatch.objects.create(dataset=dataset, atlas=Atlas.default_atlas())

        # Set current batch
        dataset.current_preprocessing_batch = batch
        dataset.save(update_fields=['current_preprocessing_batch'])

        # Dispatch task, return task id
        preprocess_images.delay(batch.id)
        return Response(PreprocessingBatchSerializer(batch).data)

    @swagger_auto_schema(
        operation_description='Run analysis on a dataset.',
        request_body=no_body,
        responses={200: PreprocessResponseSerializer()},
    )
    @action(detail=True, methods=['POST'])
    def utm_analysis(self, request, pk: str):
        dataset: Dataset = self.get_object()

        # Ensure preprocessing was previously run
        if dataset.current_preprocessing_batch is None:
            raise serializers.ValidationError('Preprocessing must be run first.')

        # Ensure analysis isn't already running
        if dataset.current_analysis_result and dataset.current_analysis_result.currently_running():
            raise serializers.ValidationError('Analysis currently running.')

        # Create analysis result
        analysis: AnalysisResult = AnalysisResult.objects.create(
            preprocessing_batch=dataset.current_preprocessing_batch
        )

        # Set current analysis result
        dataset.current_analysis_result = analysis
        dataset.save()

        # Dispatch task
        run_utm.delay(analysis.id)
        return Response(None, status=status.HTTP_204_NO_CONTENT)

    @swagger_auto_schema(
        operation_description='Retrieve all dataset images.',
        query_serializer=LimitOffsetSerializer(),
    )
    @action(detail=True, methods=['GET'])
    def images(self, request, pk: str):
        dataset: Dataset = self.get_object()
        images = Image.objects.filter(dataset=dataset).order_by('name')
        return self.get_paginated_response(
            ImageSerializer(self.paginate_queryset(images), many=True).data
        )

    @swagger_auto_schema(
        operation_description='Create Upload Batch.',
        request_body=CreateBatchSerializer(),
    )
    @action(detail=True, methods=['POST'])
    def upload_batch(self, request, pk):
        serializer = CreateBatchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        dataset: Dataset = self.get_object()
        csvfile = codecs.iterdecode(serializer.validated_data['csvfile'], 'utf-8')

        # Catch if upload doesn't contain any unique images
        try:
            batch = load_batch_from_csv(csvfile, dataset=dataset)
        except IntegrityError:
            raise serializers.ValidationError('No new images (all included images already exist)')

        serializer = UploadBatchSerializer(batch)
        return Response(serializer.data, status=201)

    @swagger_auto_schema(
        operation_description="List this dataset's upload batches.",
        query_serializer=LimitOffsetSerializer(),
        responses={200: UploadBatchSerializer(many=True)},
    )
    @action(detail=True, methods=['GET'])
    def upload_batches(self, request, pk):
        dataset: Dataset = self.get_object()
        queryset = UploadBatch.objects.filter(dataset_id=dataset.id)

        # Paginate and return
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = UploadBatchSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = UploadBatchSerializer(queryset, many=True)
        return Response(serializer.data)
