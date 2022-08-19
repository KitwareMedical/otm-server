from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from rest_framework import mixins, serializers
from rest_framework.decorators import action
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from optimal_transport_morphometry.core.models import (
    Dataset,
    FeatureImage,
    JacobianImage,
    PreprocessingBatch,
    RegisteredImage,
    SegmentedImage,
)
from optimal_transport_morphometry.core.models.image import Image
from optimal_transport_morphometry.core.rest.image import ImageSerializer
from optimal_transport_morphometry.core.rest.serializers import LimitOffsetSerializer

PREPROCESSED_IMAGE_FIELDS = [
    'id',
    'created',
    'modified',
    'blob',
    'atlas',
    'source_image',
    'preprocessing_batch',
]


class FeatureImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeatureImage
        fields = PREPROCESSED_IMAGE_FIELDS + ['downsample_factor']


class JacobianImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = JacobianImage
        fields = ['id', 'created', 'modified', 'blob']
        fields = PREPROCESSED_IMAGE_FIELDS


class RegisteredImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegisteredImage
        fields = PREPROCESSED_IMAGE_FIELDS + ['registration_type']


class SegmentedImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = SegmentedImage
        fields = PREPROCESSED_IMAGE_FIELDS


class PreprocessingBatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = PreprocessingBatch
        fields = ['id', 'created', 'modified', 'dataset', 'status', 'error_message']


class PreprocessingBatchDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = PreprocessingBatch
        fields = [
            'id',
            'created',
            'modified',
            'dataset',
            'status',
            'error_message',
            'current_image_name',
            'progress',
            'expected_image_count',
        ]

    current_image_name = serializers.CharField(required=False, default=None)
    progress = serializers.FloatField()
    expected_image_count = serializers.IntegerField()


class ImageGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Image
        new_fields = ['registered', 'jacobian', 'segmented', 'feature']
        fields = ImageSerializer.Meta.fields + new_fields
        read_only_fields = ImageSerializer.Meta.fields + new_fields

    registered = RegisteredImageSerializer(allow_null=True)
    jacobian = JacobianImageSerializer(allow_null=True)
    segmented = SegmentedImageSerializer(allow_null=True)
    feature = FeatureImageSerializer(allow_null=True)


class PreprocessingBatchViewSet(mixins.RetrieveModelMixin, GenericViewSet):
    queryset = PreprocessingBatch.objects.select_related('dataset').all()

    serializer_class = PreprocessingBatchSerializer
    serializer_detail_class = PreprocessingBatchDetailSerializer
    pagination_class = LimitOffsetPagination

    def get_queryset(self):
        return PreprocessingBatch.objects.filter(
            dataset__in=Dataset.visible_datasets(self.request.user)
        )

    def retrieve(self, request, pk: str):
        queryset = self.filter_queryset(self.get_queryset())
        batch: PreprocessingBatch = get_object_or_404(queryset, pk=pk)

        # Compute progress by counting all preprocessed images,
        # compared against the total expected image count
        batch.expected_image_count = batch.dataset.images.count() * 4.0
        batch.progress = (
            FeatureImage.objects.filter(preprocessing_batch=batch).count()
            + JacobianImage.objects.filter(preprocessing_batch=batch).count()
            + RegisteredImage.objects.filter(preprocessing_batch=batch).count()
            + SegmentedImage.objects.filter(preprocessing_batch=batch).count()
        ) / batch.expected_image_count

        # Add image currently being worked on
        batch.current_image_name = getattr(batch.current_image(), 'name', None)

        self.check_object_permissions(self.request, batch)
        serializer = PreprocessingBatchDetailSerializer(batch)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description='Retrieve the images from a preprocessing batch,'
        ' as annotated onto each source image.',
        query_serializer=LimitOffsetSerializer,
    )
    @action(detail=True, methods=['GET'])
    def images(self, request, pk: str):
        batch: PreprocessingBatch = self.get_object()
        batch_images = self.paginate_queryset(batch.source_images().order_by('name'))

        # Create map and start assigning processed images to each
        # We do this so we can make ~4 queries, as opposed to O(n) queries
        image_map = {im.id: im for im in batch_images}
        image_classes = [
            (RegisteredImage, 'registered'),
            (JacobianImage, 'jacobian'),
            (SegmentedImage, 'segmented'),
            (FeatureImage, 'feature'),
        ]
        for klass, key in image_classes:
            qs = klass.objects.filter(source_image__in=batch_images)
            for image in qs.iterator():
                setattr(image_map[image.source_image_id], key, image)

        serializer = ImageGroupSerializer(image_map.values(), many=True)
        return self.get_paginated_response(serializer.data)
