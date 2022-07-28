from django.contrib import admin

from optimal_transport_morphometry.core.models import PendingUpload, UploadBatch


@admin.register(PendingUpload)
class PendingUploadAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'batch']
    list_display_links = ['id', 'name']


@admin.register(UploadBatch)
class UploadBatchAdmin(admin.ModelAdmin):
    list_display = ['id', 'dataset', 'created', 'is_complete']
    list_display_links = ['id']
