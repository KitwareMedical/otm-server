from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django_filters import rest_framework as filters
from rest_framework import serializers
from rest_framework.decorators import action
from rest_framework.mixins import ListModelMixin
from rest_framework.permissions import AllowAny
from rest_framework.viewsets import GenericViewSet

from optimal_transport_morphometry.core.models import RegisteredImage

from .atlas import AtlasSerializer
from .image import ImageSerializer


class RegisteredImageSerializer(serializers.ModelSerializer):
    atlas = AtlasSerializer()
    source_image = ImageSerializer()

    class Meta:
        model = RegisteredImage
        fields = ['id', 'source_image', 'atlas', 'created', 'modified', 'registration_type']


class RegisteredImageViewSet(ListModelMixin, GenericViewSet):
    queryset = RegisteredImage.objects.select_related('atlas', 'source_image')

    permission_classes = [AllowAny]
    serializer_class = RegisteredImageSerializer

    filter_backends = [filters.DjangoFilterBackend]
    filterset_fields = ['source_image', 'source_image__dataset']

    @action(detail=True)
    def download(self, request, pk=None):
        image = get_object_or_404(RegisteredImage, pk=pk)
        return HttpResponseRedirect(image.blob.url)
