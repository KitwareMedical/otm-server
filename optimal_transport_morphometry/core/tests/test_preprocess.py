import pytest

from optimal_transport_morphometry.core.models.dataset import Dataset


@pytest.mark.django_db
def test_dispatch_preprocess(user, api_client, dataset_factory):
    api_client.force_authenticate(user)

    dataset: Dataset = dataset_factory(owner=user)
    r = api_client.post(f'/api/v1/datasets/{dataset.id}/preprocess')

    # Assert resp
    assert r.status_code == 200
    assert 'task_id' in r.json()

    # Assert preprocessing status
    dataset.refresh_from_db()
    assert dataset.preprocessing_status == Dataset.ProcessStatus.RUNNING


@pytest.mark.django_db
def test_dispatch_preprocess_existing(user, api_client, dataset_factory):
    api_client.force_authenticate(user)

    dataset: Dataset = dataset_factory(owner=user)
    api_client.post(f'/api/v1/datasets/{dataset.id}/preprocess')
    r = api_client.post(f'/api/v1/datasets/{dataset.id}/preprocess')

    # Assert resp
    assert r.status_code == 400
    assert r.json() == ['Preprocessing currently running.']

    # Assert preprocessing status
    dataset.refresh_from_db()
    assert dataset.preprocessing_status == Dataset.ProcessStatus.RUNNING
