from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from optimal_transport_morphometry.core.models import Atlas, Dataset
from optimal_transport_morphometry.core.tasks import preprocess_images


class PreprocessSerializer(serializers.Serializer):
    atlas = serializers.IntegerField(required=False)
    atlas_csf = serializers.IntegerField(required=False)
    atlas_grey = serializers.IntegerField(required=False)
    atlas_white = serializers.IntegerField(required=False)
    dataset = serializers.IntegerField()


class PreprocessResponseSerializer(serializers.Serializer):
    task_id = serializers.CharField()


def _load_atlas(serializer, key: str) -> Atlas:
    passed_id = serializer.validated_data.get(key)
    if passed_id:
        return get_object_or_404(Atlas, pk=passed_id)

    name = {
        'atlas': 'T1.nii',
        'atlas_csf': 'csf.nii',
        'atlas_grey': 'grey.nii',
        'atlas_white': 'white.nii',
    }[key]
    return get_object_or_404(Atlas, name=name)


class PreprocessingViewSet(GenericViewSet):
    queryset = Dataset.objects.all()

    permission_classes = [AllowAny]
    serializer_class = PreprocessSerializer

    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Validate that the IDs are good before we invoke the celery task
        atlas = _load_atlas(serializer, 'atlas')
        atlas_csf = _load_atlas(serializer, 'atlas_csf')
        atlas_grey = _load_atlas(serializer, 'atlas_grey')
        atlas_white = _load_atlas(serializer, 'atlas_white')
        dataset_id = serializer.validated_data['dataset']
        # TODO get better error messages than what get_object_or_404 provides us
        get_object_or_404(Dataset, pk=dataset_id)

        task = preprocess_images.delay(
            atlas.id, atlas_csf.id, atlas_grey.id, atlas_white.id, dataset_id
        )
        serializer = PreprocessResponseSerializer({'task_id': task.id})
        return Response(serializer.data)
