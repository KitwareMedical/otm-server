from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django_filters import rest_framework as filters
from rest_framework import serializers
from rest_framework.decorators import action
from rest_framework.mixins import ListModelMixin
from rest_framework.permissions import AllowAny
from rest_framework.viewsets import GenericViewSet

from optimal_transport_morphometry.core.models import JacobianImage

from .atlas import AtlasSerializer
from .image import ImageSerializer


class JacobianImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = JacobianImage
        fields = ['id', 'created', 'modified', 'blob']


class ExtendedJacobianImageSerializer(serializers.ModelSerializer):
    atlas = AtlasSerializer()
    source_image = ImageSerializer()

    class Meta:
        model = JacobianImage
        fields = JacobianImageSerializer.Meta.fields + ['atlas' + 'source_image']


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
