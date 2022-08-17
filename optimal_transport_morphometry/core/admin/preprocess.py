from django.contrib import admin

from optimal_transport_morphometry.core.models import (
    FeatureImage,
    JacobianImage,
    PreprocessingBatch,
    RegisteredImage,
    SegmentedImage,
)


@admin.register(PreprocessingBatch)
class PreprocessingBatchAdmin(admin.ModelAdmin):
    list_display = ['id', 'created', 'status', 'dataset', 'error_message']
    list_display_links = ['id']


class CommonAdmin(admin.ModelAdmin):
    list_display = ['id', 'atlas', 'blob', 'source_image', 'preprocessing_batch']
    list_display_links = ['id']


@admin.register(JacobianImage)
class JacobianImageAdmin(CommonAdmin):
    pass


@admin.register(SegmentedImage)
class SegmentedImageAdmin(CommonAdmin):
    pass


@admin.register(FeatureImage)
class FeatureImageAdmin(CommonAdmin):
    list_display = CommonAdmin.list_display + ['downsample_factor']


@admin.register(RegisteredImage)
class RegisteredImageAdmin(admin.ModelAdmin):
    list_display = CommonAdmin.list_display + ['registration_type']
