import pytest

from optimal_transport_morphometry.core.models import AnalysisResult, Dataset, PreprocessingBatch


@pytest.fixture
def preprocessed_dataset(user, dataset_factory, preprocessing_batch_factory):
    dataset: Dataset = dataset_factory(owner=user)
    batch: PreprocessingBatch = preprocessing_batch_factory(
        dataset=dataset, status=PreprocessingBatch.Status.FINISHED
    )
    dataset.current_preprocessing_batch = batch
    dataset.save()

    return dataset


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
def test_dispatch_utm_analysis_no_preprocess(user, api_client, dataset_factory):
    api_client.force_authenticate(user)
    dataset: Dataset = dataset_factory(owner=user)
    r = api_client.post(f'/api/v1/datasets/{dataset.id}/utm_analysis')

    # Assert resp
    assert r.status_code == 400
    assert r.json() == ['Preprocessing must be run first.']


@pytest.mark.django_db
def test_dispatch_utm_analysis(api_client, preprocessed_dataset):
    dataset: Dataset = preprocessed_dataset

    api_client.force_authenticate(dataset.owner)
    r = api_client.post(f'/api/v1/datasets/{dataset.id}/utm_analysis')

    # Assert resp
    assert r.status_code == 204

    # Assert preprocessing status
    dataset.refresh_from_db()
    assert dataset.current_analysis_result is not None

    # Implicit assert of existence
    analysis: AnalysisResult = AnalysisResult.objects.get(id=dataset.current_analysis_result.id)
    assert analysis.preprocessing_batch == dataset.current_preprocessing_batch


@pytest.mark.django_db
def test_dispatch_utm_analysis_existing(api_client, preprocessed_dataset):
    dataset: Dataset = preprocessed_dataset
    api_client.force_authenticate(dataset.owner)

    # Dispatch first analysis
    api_client.post(f'/api/v1/datasets/{dataset.id}/utm_analysis')

    # Fetch current analysis
    dataset.refresh_from_db()
    analysis: AnalysisResult = dataset.current_analysis_result
    assert analysis.status == AnalysisResult.Status.PENDING

    # Attempt to dispatch second analysis
    r = api_client.post(f'/api/v1/datasets/{dataset.id}/utm_analysis')

    # Assert resp
    assert r.status_code == 400
    assert r.json() == ['Analysis currently running.']

    # Assert preprocessing status
    dataset.refresh_from_db()
    assert dataset.current_analysis_result == analysis
    assert dataset.current_analysis_result.status == AnalysisResult.Status.PENDING
