from __future__ import annotations

from pathlib import Path

from composed_configuration import (
    ComposedConfiguration,
    ConfigMixin,
    DevelopmentBaseConfiguration,
    HerokuProductionBaseConfiguration,
    ProductionBaseConfiguration,
    TestingBaseConfiguration,
)


class OptimalTransportMorphometryConfig(ConfigMixin):
    WSGI_APPLICATION = 'optimal_transport_morphometry.wsgi.application'
    ROOT_URLCONF = 'optimal_transport_morphometry.urls'

    BASE_DIR = Path(__file__).resolve(strict=True).parent.parent

    @staticmethod
    def before_binding(configuration: ComposedConfiguration) -> None:
        configuration.INSTALLED_APPS += [
            'optimal_transport_morphometry.core.apps.CoreConfig',
            's3_file_field',
        ]


class DevelopmentConfiguration(OptimalTransportMorphometryConfig, DevelopmentBaseConfiguration):
    pass


class TestingConfiguration(OptimalTransportMorphometryConfig, TestingBaseConfiguration):
    pass


class ProductionConfiguration(OptimalTransportMorphometryConfig, ProductionBaseConfiguration):
    pass


class HerokuProductionConfiguration(OptimalTransportMorphometryConfig, HerokuProductionBaseConfiguration):
    pass
