from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from optimal_transport_morphometry.core.models import Atlas, Dataset
from optimal_transport_morphometry.core.tasks import preprocess_images


class PreprocessSerializer(serializers.Serializer):
    atlas = serializers.IntegerField()
    atlas_csf = serializers.IntegerField()
    atlas_grey = serializers.IntegerField()
    atlas_white = serializers.IntegerField()
    dataset = serializers.IntegerField()


class PreprocessResponseSerializer(serializers.Serializer):
    task_id = serializers.CharField()


class PreprocessingViewSet(GenericViewSet):
    queryset = Dataset.objects.all()

    permission_classes = [AllowAny]
    serializer_class = PreprocessSerializer

    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Validate that the IDs are good before we invoke the celery task
        atlas_id = serializer.validated_data['atlas']
        atlas_csf_id = serializer.validated_data['atlas_csf']
        atlas_grey_id = serializer.validated_data['atlas_grey']
        atlas_white_id = serializer.validated_data['atlas_white']
        dataset_id = serializer.validated_data['dataset']
        # TODO get better error messages than what get_object_or_404 provides us
        get_object_or_404(Atlas, pk=atlas_id)
        get_object_or_404(Atlas, pk=atlas_csf_id)
        get_object_or_404(Atlas, pk=atlas_grey_id)
        get_object_or_404(Atlas, pk=atlas_white_id)
        get_object_or_404(Dataset, pk=dataset_id)

        task = preprocess_images.delay(
            atlas_id, atlas_csf_id, atlas_grey_id, atlas_white_id, dataset_id
        )
        serializer = PreprocessResponseSerializer({'task_id': task.id})
        return Response(serializer.data)
