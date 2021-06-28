from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from optimal_transport_morphometry.core.models import Dataset
from optimal_transport_morphometry.core.tasks import run_utm


class UTMAnalysisSerializer(serializers.Serializer):
    dataset = serializers.IntegerField()


class PreprocessResponseSerializer(serializers.Serializer):
    task_id = serializers.CharField()


class UTMAnalysisViewSet(GenericViewSet):
    queryset = Dataset.objects.all()

    permission_classes = [AllowAny]
    serializer_class = UTMAnalysisSerializer

    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Validate that the IDs are good before we invoke the celery task
        dataset_id = serializer.validated_data['dataset']

        # TODO get better error messages than what get_object_or_404 provides us
        get_object_or_404(Dataset, pk=dataset_id)

        task = run_utm.delay(dataset_id)
        serializer = PreprocessResponseSerializer({'task_id': task.id})
        return Response(serializer.data)
