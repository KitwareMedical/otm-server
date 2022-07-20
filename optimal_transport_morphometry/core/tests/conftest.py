import pytest
from pytest_factoryboy import register
from rest_framework.test import APIClient

from .factories import (
    DatasetFactory,
    FeatureImageFactory,
    ImageFactory,
    JacobianImageFactory,
    RegisteredImageFactory,
    SegmentedImageFactory,
    T1AtlasFactory,
    UserFactory,
)


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def authenticated_api_client(user) -> APIClient:
    client = APIClient()
    client.force_authenticate(user=user)
    return client


register(DatasetFactory)
register(UserFactory)
register(ImageFactory)
register(FeatureImageFactory)
register(JacobianImageFactory)
register(RegisteredImageFactory)
register(SegmentedImageFactory)
register(T1AtlasFactory)
