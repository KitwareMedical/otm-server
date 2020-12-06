from django.db import transaction
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django_filters import rest_framework as filters
from drf_yasg2.utils import swagger_auto_schema
from rest_framework import serializers
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from optimal_transport_morphometry.core.models import Image, PendingUpload


class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Image
        fields = ['id', 'name', 'type', 'dataset', 'patient', 'metadata']
        read_only_fields = ['type', 'dataset', 'patient', 'metadata']


class CreateImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Image
        fields = ['blob', 'pending_upload']

    pending_upload = serializers.IntegerField()


class ImageViewSet(ModelViewSet):
    queryset = Image.objects.all()

    permission_classes = [AllowAny]
    serializer_class = ImageSerializer

    filter_backends = [filters.DjangoFilterBackend]
    filterset_fields = ['name']

    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        image = get_object_or_404(Image, pk=pk)
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
        upload = get_object_or_404(PendingUpload, pk=serializer.validated_data['pending_upload'])
        blob = serializer.validated_data['blob']

        # TODO validate existence of key in storage
        image = Image.objects.create(
            blob=blob, patient=upload.patient, name=upload.name, metadata=upload.metadata
        )
        upload.delete()
        serializer = self.get_serializer(image)
        return Response(serializer.data)
