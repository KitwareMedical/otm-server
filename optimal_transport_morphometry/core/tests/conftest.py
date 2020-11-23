import pytest
from pytest_factoryboy import register
from rest_framework.test import APIClient

from .factories import DatasetFactory, ImageFactory, UserFactory


@pytest.fixture
def api_client():
    return APIClient()


register(DatasetFactory)
register(ImageFactory)
register(UserFactory)
