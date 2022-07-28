from rest_framework import mixins, serializers
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.viewsets import GenericViewSet

from optimal_transport_morphometry.core.models import Dataset, PendingUpload


class PendingUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = PendingUpload
        fields = ['id', 'name']


class PendingUploadViewSet(mixins.RetrieveModelMixin, GenericViewSet):
    queryset = PendingUpload.objects.all()

    permission_classes = [IsAuthenticatedOrReadOnly]
    serializer_class = PendingUploadSerializer

    def get_queryset(self):
        datasets = Dataset.visible_datasets(self.request.user)
        return self.queryset.filter(batch__dataset__in=datasets)
