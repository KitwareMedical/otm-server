from django_filters import rest_framework as filters
from drf_yasg.utils import swagger_auto_schema
from rest_framework import parsers, serializers
from rest_framework.decorators import action
from rest_framework.mixins import RetrieveModelMixin
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from optimal_transport_morphometry.core.models import Dataset, PendingUpload, UploadBatch
from optimal_transport_morphometry.core.rest.pending_upload import PendingUploadSerializer
from optimal_transport_morphometry.core.rest.serializers import LimitOffsetSerializer


class PendingUploadListRequestSerializer(LimitOffsetSerializer):
    name = serializers.CharField(required=False)


class UploadBatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = UploadBatch
        fields = ['id', 'created', 'dataset']


class UploadBatchViewSet(RetrieveModelMixin, GenericViewSet):
    queryset = UploadBatch.objects.all()

    permission_classes = [AllowAny]
    serializer_class = UploadBatchSerializer
    parser_classes = [parsers.JSONParser, parsers.MultiPartParser]

    filter_backends = [filters.DjangoFilterBackend]
    filterset_fields = ['dataset']

    def get_queryset(self):
        datasets = Dataset.visible_datasets(self.request.user)
        return self.queryset.filter(dataset__in=datasets)

    @swagger_auto_schema(
        operation_description='List pending uploads for a batch.',
        query_serializer=PendingUploadListRequestSerializer(),
        responses={200: PendingUploadSerializer(many=True)},
    )
    @action(detail=True, methods=['GET'])
    def pending(self, request, pk):
        serializer = PendingUploadListRequestSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        # Retrieve all pending uploads
        batch: UploadBatch = self.get_object()
        queryset = PendingUpload.objects.filter(batch_id=batch.id)

        # Filter by name if desired
        name = serializer.validated_data.get('name')
        if name is not None:
            queryset = queryset.filter(name__icontains=name)

        # Paginate and return
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = PendingUploadSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = PendingUploadSerializer(queryset, many=True)
        return Response(serializer.data)
