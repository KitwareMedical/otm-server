from django_filters import rest_framework as filters
from rest_framework import serializers
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.viewsets import ModelViewSet

from optimal_transport_morphometry.core.models import Dataset


class DatasetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dataset
        fields = ['id', 'name', 'description']


class CreateBatchSerializer(serializers.Serializer):
    csvfile = serializers.FileField(allow_empty_file=False, max_length=1024 * 1024)


class DatasetViewSet(ModelViewSet):
    queryset = Dataset.objects.all()

    permission_classes = [IsAuthenticatedOrReadOnly]
    serializer_class = DatasetSerializer

    filter_backends = [filters.DjangoFilterBackend]
    filterset_fields = ['name']

    pagination_class = PageNumberPagination
