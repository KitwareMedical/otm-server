from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django_filters import rest_framework as filters
from rest_framework import serializers
from rest_framework.decorators import action
from rest_framework.mixins import ListModelMixin
from rest_framework.permissions import AllowAny
from rest_framework.viewsets import GenericViewSet

from optimal_transport_morphometry.core.models import (
    FeatureImage,
    JacobianImage,
    RegisteredImage,
    SegmentedImage,
)

from .atlas import AtlasSerializer
from .image import ImageSerializer

# ##############
# FEATURE IMAGES
# ##############


class FeatureImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeatureImage
        fields = ['id', 'created', 'modified', 'downsample_factor', 'blob']


class ExtendedFeatureImageSerializer(serializers.ModelSerializer):
    atlas = AtlasSerializer()
    source_image = ImageSerializer()

    class Meta:
        model = FeatureImage
        fields = FeatureImageSerializer.Meta.fields + ['atlas', 'source_image']


class FeatureImageViewSet(ListModelMixin, GenericViewSet):
    queryset = FeatureImage.objects.select_related('atlas', 'source_image')

    permission_classes = [AllowAny]
    serializer_class = FeatureImageSerializer

    filter_backends = [filters.DjangoFilterBackend]
    filterset_fields = ['source_image', 'source_image__dataset']

    @action(detail=True)
    def download(self, request, pk=None):
        image = get_object_or_404(FeatureImage, pk=pk)
        return HttpResponseRedirect(image.blob.url)


# ###############
# JACOBIAN IMAGES
# ###############


class JacobianImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = JacobianImage
        fields = ['id', 'created', 'modified', 'blob']


class ExtendedJacobianImageSerializer(serializers.ModelSerializer):
    atlas = AtlasSerializer()
    source_image = ImageSerializer()

    class Meta:
        model = JacobianImage
        fields = JacobianImageSerializer.Meta.fields + ['atlas', 'source_image']


class JacobianImageViewSet(ListModelMixin, GenericViewSet):
    queryset = JacobianImage.objects.select_related('atlas', 'source_image')

    permission_classes = [AllowAny]
    serializer_class = ExtendedJacobianImageSerializer

    filter_backends = [filters.DjangoFilterBackend]
    filterset_fields = ['source_image', 'source_image__dataset']

    @action(detail=True)
    def download(self, request, pk=None):
        image = get_object_or_404(JacobianImage, pk=pk)
        return HttpResponseRedirect(image.blob.url)


# #################
# REGISTERED IMAGES
# #################


class RegisteredImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegisteredImage
        fields = ['id', 'created', 'modified', 'registration_type', 'blob']


class ExtendedRegisteredImageSerializer(serializers.ModelSerializer):
    atlas = AtlasSerializer()
    source_image = ImageSerializer()

    class Meta:
        model = RegisteredImage
        fields = RegisteredImageSerializer.Meta.fields + ['atlas', 'source_image']


class RegisteredImageViewSet(ListModelMixin, GenericViewSet):
    queryset = RegisteredImage.objects.select_related('atlas', 'source_image')

    permission_classes = [AllowAny]
    serializer_class = ExtendedRegisteredImageSerializer

    filter_backends = [filters.DjangoFilterBackend]
    filterset_fields = ['source_image', 'source_image__dataset']

    @action(detail=True)
    def download(self, request, pk=None):
        image = get_object_or_404(RegisteredImage, pk=pk)
        return HttpResponseRedirect(image.blob.url)


# ################
# SEGMENTED IMAGES
# ################


class SegmentedImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = SegmentedImage
        fields = ['id', 'created', 'modified', 'blob']


class ExtendedSegmentedImageSerializer(serializers.ModelSerializer):
    atlas = AtlasSerializer()
    source_image = ImageSerializer()

    class Meta:
        model = SegmentedImage
        fields = SegmentedImageSerializer.Meta.fields + ['atlas', 'source_image']


class SegmentedImageViewSet(ListModelMixin, GenericViewSet):
    queryset = SegmentedImage.objects.select_related('atlas', 'source_image')

    permission_classes = [AllowAny]
    serializer_class = ExtendedSegmentedImageSerializer

    filter_backends = [filters.DjangoFilterBackend]
    filterset_fields = ['source_image', 'source_image__dataset']

    @action(detail=True)
    def download(self, request, pk=None):
        image = get_object_or_404(SegmentedImage, pk=pk)
        return HttpResponseRedirect(image.blob.url)
