from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from optimal_transport_morphometry.core.models import Atlas, Dataset
from optimal_transport_morphometry.core.tasks import preprocess_images


class PreprocessSerializer(serializers.Serializer):
    atlas = serializers.IntegerField()
    dataset = serializers.IntegerField()


class PreprocessingViewSet(GenericViewSet):
    queryset = Dataset.objects.all()

    permission_classes = [AllowAny]
    serializer_class = PreprocessSerializer

    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Validate that the IDs are good before we invoke the celery task
        atlas_id = serializer.validated_data['atlas']
        dataset_id = serializer.validated_data['dataset']
        get_object_or_404(Atlas, pk=atlas_id)
        get_object_or_404(Dataset, pk=dataset_id)

        task = preprocess_images.delay(atlas_id, dataset_id)
        print(task)
        return Response()
