from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django_filters import rest_framework as filters
from rest_framework import serializers
from rest_framework.decorators import action
from rest_framework.mixins import ListModelMixin
from rest_framework.permissions import AllowAny
from rest_framework.viewsets import GenericViewSet

from optimal_transport_morphometry.core.models import JacobianImage


class JacobianImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = JacobianImage
        fields = ['id', 'source_image', 'atlas', 'created', 'modified']


class JacobianImageViewSet(ListModelMixin, GenericViewSet):
    queryset = JacobianImage.objects.all()

    permission_classes = [AllowAny]
    serializer_class = JacobianImageSerializer

    filter_backends = [filters.DjangoFilterBackend]
    filterset_fields = ['source_image', 'source_image__dataset']

    @action(detail=True)
    def download(self, request, pk=None):
        image = get_object_or_404(JacobianImage, pk=pk)
        return HttpResponseRedirect(image.blob.url)
