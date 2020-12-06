import codecs

from django.shortcuts import get_object_or_404
from django_filters import rest_framework as filters
from rest_framework import parsers, serializers
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from optimal_transport_morphometry.core.batch_parser import load_batch_from_csv
from optimal_transport_morphometry.core.models import Dataset, PendingUpload, UploadBatch


class PendingUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = PendingUpload
        fields = ['id', 'patient', 'name']


class UploadBatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = UploadBatch
        fields = ['id', 'created', 'dataset']


class CreateBatchSerializer(serializers.Serializer):
    dataset = serializers.IntegerField()
    csvfile = serializers.FileField(allow_empty_file=False, max_length=1024 * 1024)


class UploadBatchViewSet(ModelViewSet):
    queryset = UploadBatch.objects.all()

    permission_classes = [AllowAny]
    serializer_class = UploadBatchSerializer
    parser_classes = [parsers.JSONParser, parsers.MultiPartParser]

    filter_backends = [filters.DjangoFilterBackend]
    filterset_fields = ['dataset']

    def create(self, request):
        serializer = CreateBatchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        dataset = get_object_or_404(Dataset, pk=serializer.validated_data['dataset'])
        csvfile = codecs.iterdecode(serializer.validated_data['csvfile'], 'utf-8')
        batch = load_batch_from_csv(csvfile, dest=dataset)
        serializer = UploadBatchSerializer(batch)
        return Response(serializer.data, status=201)
