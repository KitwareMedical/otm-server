from django.contrib import admin

from optimal_transport_morphometry.core.models import Image


@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'type', 'blob', 'dataset', 'patient', 'size']
    list_display_links = ['id', 'name']
