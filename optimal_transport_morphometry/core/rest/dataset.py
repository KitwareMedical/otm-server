from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django_filters import rest_framework as filters
from drf_yasg.utils import swagger_auto_schema
from guardian.shortcuts import assign_perm, get_users_with_perms
from rest_framework import serializers, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from optimal_transport_morphometry.core.models import Dataset, Image
from optimal_transport_morphometry.core.rest.feature_image import FeatureImageSerializer
from optimal_transport_morphometry.core.rest.image import ImageSerializer
from optimal_transport_morphometry.core.rest.jacobian_image import JacobianImageSerializer
from optimal_transport_morphometry.core.rest.registered_image import RegisteredImageSerializer
from optimal_transport_morphometry.core.rest.segmented_image import SegmentedImageSerializer
from optimal_transport_morphometry.core.rest.user import ExistingUserSerializer, UserSerializer


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


class DatasetViewSet(ModelViewSet):
    queryset = Dataset.objects.all()

    permission_classes = [AllowAny]
    serializer_class = DatasetSerializer

    filter_backends = [filters.DjangoFilterBackend]
    filterset_fields = ['name']

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

        # Perform create
        ds = Dataset.objects.create(**serializer.validated_data, owner=request.user)
        return Response(DatasetSerializer(ds).data, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(
        operation_description='Set the collaborators of a dataset.',
        request_body=ExistingUserSerializer(many=True),
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
        serializer: ExistingUserSerializer = ExistingUserSerializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)

        # Assign perm to each user
        for userdict in serializer.validated_data:
            user: User = User.objects.get(username=userdict['username'])
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
