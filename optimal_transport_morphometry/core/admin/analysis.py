from django.contrib import admin

from optimal_transport_morphometry.core.models import AnalysisResult


@admin.register(AnalysisResult)
class AnalysisResultAdmin(admin.ModelAdmin):
    list_display = ['id', 'created', 'preprocessing_batch', 'status']
    list_display_links = ['id']
    list_select_related = True

    fields = [
        'preprocessing_batch',
        'status',
        'error_message',
        'zip_file',
        'data',
    ]
