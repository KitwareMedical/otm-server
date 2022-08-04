from __future__ import annotations

from pathlib import Path

from composed_configuration import (
    CeleryMixin,
    ComposedConfiguration,
    ConfigMixin,
    DevelopmentBaseConfiguration,
    HerokuProductionBaseConfiguration,
    ProductionBaseConfiguration,
    S3StorageMixin,
    SmtpEmailMixin,
    TestingBaseConfiguration,
)
from configurations import values

_pkg = 'optimal_transport_morphometry'


class OptimalTransportMorphometryMixin(ConfigMixin):
    WSGI_APPLICATION = f'{_pkg}.wsgi.application'
    ROOT_URLCONF = f'{_pkg}.urls'

    BASE_DIR = Path(__file__).resolve(strict=True).parent.parent

    CELERY_TASK_ACKS_LATE = True

    @staticmethod
    def mutate_configuration(configuration: ComposedConfiguration) -> None:
        # Install local apps first, to ensure any overridden resources are found first
        configuration.INSTALLED_APPS = [
            f'{_pkg}.core.apps.CoreConfig',
        ] + configuration.INSTALLED_APPS

        # Install additional apps
        configuration.INSTALLED_APPS += [
            'guardian',
            's3_file_field',
        ]

        # Add additional auth backends
        configuration.AUTHENTICATION_BACKENDS += ['guardian.backends.ObjectPermissionBackend']

        #
        configuration.REST_FRAMEWORK.update(
            {
                'DEFAULT_PAGINATION_CLASS': f'{_pkg}.core.pagination.BoundedLimitOffsetPagination',
                # TODO we can remove the line below once OAuth login is working in client
                'DEFAULT_PERMISSION_CLASSES': ['rest_framework.permissions.AllowAny'],
            }
        )


class DevelopmentConfiguration(OptimalTransportMorphometryMixin, DevelopmentBaseConfiguration):
    pass


class TestingConfiguration(OptimalTransportMorphometryMixin, TestingBaseConfiguration):
    pass


class ProductionConfiguration(OptimalTransportMorphometryMixin, ProductionBaseConfiguration):
    pass


class HerokuProductionConfiguration(
    OptimalTransportMorphometryMixin, HerokuProductionBaseConfiguration
):
    pass


class CeleryWorkerConfiguration(
    OptimalTransportMorphometryMixin, CeleryMixin, SmtpEmailMixin, S3StorageMixin
):
    # Require `DJANGO_CELERY_BROKER_URL` environment variable
    CELERY_BROKER_URL = values.Value(environ_name='CELERY_BROKER_URL', environ_required=True)
