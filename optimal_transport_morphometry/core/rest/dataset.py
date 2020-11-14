from django_filters import rest_framework as filters
from rest_framework import serializers
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.viewsets import ReadOnlyModelViewSet

from optimal_transport_morphometry.core.models import Image


class DatasetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Image
        fields = ['id', 'name', 'description']


class ImageViewSet(ReadOnlyModelViewSet):
    queryset = Image.objects.all()

    permission_classes = [IsAuthenticatedOrReadOnly]
    serializer_class = DatasetSerializer

    filter_backends = [filters.DjangoFilterBackend]
    filterset_fields = ['name']

    pagination_class = PageNumberPagination
