import pytest

from optimal_transport_morphometry.core.models import Dataset


@pytest.mark.django_db
def test_dispatch_preprocess(user, api_client, dataset_factory, image_factory):
    api_client.force_authenticate(user)

    dataset: Dataset = dataset_factory(owner=user)
    image_factory(dataset=dataset)
    r = api_client.post(f'/api/v1/datasets/{dataset.id}/preprocess')

    # Assert resp
    assert r.status_code == 200

    # Get batch
    batch_id = r.json()['id']
    r = api_client.get(f'/api/v1/preprocessing_batches/{batch_id}')
    assert r.status_code == 200


@pytest.mark.django_db
def test_dispatch_preprocess_empty(user, api_client, dataset_factory):
    api_client.force_authenticate(user)

    dataset: Dataset = dataset_factory(owner=user)
    r = api_client.post(f'/api/v1/datasets/{dataset.id}/preprocess')

    # Assert resp
    assert r.status_code == 400
    assert r.json() == ['Cannot run preprocessing on empty dataset.']


@pytest.mark.django_db
def test_dispatch_preprocess_existing(user, api_client, dataset_factory, image_factory):
    api_client.force_authenticate(user)

    dataset: Dataset = dataset_factory(owner=user)
    image_factory(dataset=dataset)

    api_client.post(f'/api/v1/datasets/{dataset.id}/preprocess')
    r = api_client.post(f'/api/v1/datasets/{dataset.id}/preprocess')

    # Assert resp
    assert r.status_code == 400
    assert r.json() == ['Preprocessing currently running.']


@pytest.mark.django_db
def test_dispatch_utm_analysis(user, api_client, dataset_factory):
    api_client.force_authenticate(user)

    dataset: Dataset = dataset_factory(owner=user)
    r = api_client.post(f'/api/v1/datasets/{dataset.id}/utm_analysis')

    # Assert resp
    assert r.status_code == 200
    assert 'task_id' in r.json()

    # Assert preprocessing status
    dataset.refresh_from_db()
    assert dataset.analysis_status == Dataset.ProcessStatus.RUNNING


@pytest.mark.django_db
def test_dispatch_utm_analysis_existing(user, api_client, dataset_factory):
    api_client.force_authenticate(user)

    dataset: Dataset = dataset_factory(owner=user)
    api_client.post(f'/api/v1/datasets/{dataset.id}/utm_analysis')
    r = api_client.post(f'/api/v1/datasets/{dataset.id}/utm_analysis')

    # Assert resp
    assert r.status_code == 400
    assert r.json() == ['Analysis currently running.']

    # Assert preprocessing status
    dataset.refresh_from_db()
    assert dataset.analysis_status == Dataset.ProcessStatus.RUNNING
