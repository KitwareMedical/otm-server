from django.contrib.auth.models import User
from django.db import transaction
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django_filters import rest_framework as filters
from drf_yasg.utils import swagger_auto_schema
from rest_framework import mixins, serializers
from rest_framework.decorators import action
from rest_framework.exceptions import NotAuthenticated, PermissionDenied
from rest_framework.permissions import SAFE_METHODS, BasePermission
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from optimal_transport_morphometry.core.models import Dataset, Image, PendingUpload


class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Image
        fields = ['id', 'name', 'type', 'dataset', 'metadata']
        read_only_fields = ['type', 'dataset', 'metadata']


class CreateImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Image
        fields = ['blob', 'pending_upload']

    pending_upload = serializers.IntegerField()


class ImagePermissions(BasePermission):
    def has_permission(self, request: Request, view):
        # Only endpoint that this hits is create
        # Create logic is handled in that method
        return True

    def has_object_permission(self, request: Request, view, image: Image):
        dataset: Dataset = image.dataset
        if dataset.public and request.method in SAFE_METHODS:
            return True

        user: User = request.user
        if not user.is_authenticated:
            raise NotAuthenticated()

        if dataset.access(user) is None:
            raise PermissionDenied()

        # Nothing wrong, permission allowed
        return True


class ImageViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    GenericViewSet,
):
    queryset = Image.objects.select_related('dataset').all()

    permission_classes = [ImagePermissions]
    serializer_class = ImageSerializer

    filter_backends = [filters.DjangoFilterBackend]
    filterset_fields = ['dataset']

    def get_queryset(self):
        # Get all allowed images
        datasets = Dataset.visible_datasets(self.request.user)
        return self.queryset.filter(dataset__in=datasets)

    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        image = self.get_object()
        return HttpResponseRedirect(image.blob.url)

    @transaction.atomic
    @swagger_auto_schema(
        operation_description='Create a new image.',
        request_body=CreateImageSerializer,
        responses={200: ImageSerializer},
    )
    def create(self, request):
        serializer = CreateImageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        blob = serializer.validated_data['blob']

        # Fetch upload
        upload: PendingUpload = get_object_or_404(
            PendingUpload.objects.select_related('batch__dataset'),
            pk=serializer.validated_data['pending_upload'],
        )

        # Ensure access
        dataset: Dataset = upload.batch.dataset
        if dataset.access(request.user) is None:
            raise PermissionDenied()

        # TODO validate existence of key in storage
        image = Image.objects.create(
            blob=blob,
            name=upload.name,
            metadata=upload.metadata,
            dataset=upload.batch.dataset,
        )
        upload.delete()
        serializer = self.get_serializer(image)
        return Response(serializer.data)
