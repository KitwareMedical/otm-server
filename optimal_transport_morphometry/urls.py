from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions, routers

from optimal_transport_morphometry.core import rest

router = routers.SimpleRouter(trailing_slash=False)
router.register(r'users', rest.UserViewSet)
router.register(r'atlases', rest.AtlasViewSet)
router.register(r'datasets', rest.DatasetViewSet)
router.register(r'images', rest.ImageViewSet)

# Preprocessing and Analysis
router.register(r'preprocessing_batches', rest.PreprocessingBatchViewSet)
router.register(r'analysis', rest.AnalysisResultViewSet)

# Upload
router.register(r'upload/pending', rest.PendingUploadViewSet)
router.register(r'upload/batches', rest.UploadBatchViewSet)

# OpenAPI generation
schema_view = get_schema_view(
    openapi.Info(title='Optimal Transport Morphometry', default_version='v1', description=''),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('accounts/', include('allauth.urls')),
    path('oauth/', include('oauth2_provider.urls', namespace='oauth2_provider')),
    path('admin/', admin.site.urls),
    path('api/v1/s3-upload/', include('s3_file_field.urls')),
    path('api/v1/', include(router.urls)),
    path('api/docs/redoc/', schema_view.with_ui('redoc'), name='docs-redoc'),
    path('api/docs/swagger/', schema_view.with_ui('swagger'), name='docs-swagger'),
]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [path('__debug__/', include(debug_toolbar.urls))] + urlpatterns
