from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django_filters import rest_framework as filters
from rest_framework import serializers
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.viewsets import ReadOnlyModelViewSet

from optimal_transport_morphometry.core.models import Atlas


class AtlasSerializer(serializers.ModelSerializer):
    class Meta:
        model = Atlas
        fields = ['id', 'name', 'blob']


class AtlasViewSet(ReadOnlyModelViewSet):
    queryset = Atlas.objects.all()

    permission_classes = [AllowAny]
    serializer_class = AtlasSerializer

    filter_backends = [filters.DjangoFilterBackend]
    filterset_fields = ['name']

    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        atlas = get_object_or_404(Atlas, pk=pk)
        return HttpResponseRedirect(atlas.blob.url)
