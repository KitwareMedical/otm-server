from django.contrib import admin
from guardian.admin import GuardedModelAdmin

from optimal_transport_morphometry.core.models import Dataset


@admin.register(Dataset)
class DatasetAdmin(GuardedModelAdmin):
    list_display = [
        'id',
        'name',
        'owner',
        'public',
        'current_preprocessing_batch',
        'analysis_status',
    ]
    list_display_links = ['id', 'name']
    list_filter = ['name']
    list_select_related = True

    search_fields = ['name']

    fields = [
        'name',
        'description',
        'owner',
        'public',
        'current_preprocessing_batch',
        'analysis_status',
    ]
