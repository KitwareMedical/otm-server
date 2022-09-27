from rest_framework import serializers
from rest_framework.mixins import RetrieveModelMixin
from rest_framework.permissions import AllowAny
from rest_framework.viewsets import GenericViewSet

from optimal_transport_morphometry.core.models import AnalysisResult, Dataset


class AnalysisResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnalysisResult
        fields = [
            'id',
            'created',
            'modified',
            'preprocessing_batch',
            'status',
            'error_message',
            'zip_file',
            'data',
        ]


class AnalysisResultViewSet(RetrieveModelMixin, GenericViewSet):
    queryset = AnalysisResult.objects.select_related('preprocessing_batch__dataset').all()

    def get_queryset(self):
        return AnalysisResult.objects.filter(
            preprocessing_batch__dataset__in=Dataset.visible_datasets(self.request.user)
        )

    permission_classes = [AllowAny]
    serializer_class = AnalysisResultSerializer
