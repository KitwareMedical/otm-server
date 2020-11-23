from django.shortcuts import get_object_or_404
from drf_yasg2.utils import swagger_auto_schema
from rest_framework import serializers
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.viewsets import ReadOnlyModelViewSet

from optimal_transport_morphometry.core.models import PendingUpload, UploadBatch


class PendingUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = PendingUpload
        fields = ['id', 'patient', 'name']


class PendingUploadListRequestSerializer(serializers.Serializer):
    batch = serializers.IntegerField()


class PendingUploadViewSet(ReadOnlyModelViewSet):
    queryset = PendingUpload.objects.all()

    permission_classes = [IsAuthenticatedOrReadOnly]
    serializer_class = PendingUploadSerializer

    @swagger_auto_schema(
        operation_description='List pending uploads for a batch.',
        query_serializer=PendingUploadListRequestSerializer,
        responses={200: PendingUploadSerializer(many=True)},
    )
    def list(self, request):
        serializer = PendingUploadListRequestSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        batch = get_object_or_404(UploadBatch, pk=serializer.validated_data['batch'])
        qs = self.queryset.filter(batch=batch)
        page = self.paginate_queryset(qs)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)
