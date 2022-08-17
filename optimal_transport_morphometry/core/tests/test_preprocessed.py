import pytest

from optimal_transport_morphometry.core.models import PreprocessingBatch


@pytest.mark.django_db
def test_fetch_preprocessed_images(
    user,
    api_client,
    dataset_factory,
    preprocessing_batch_factory,
    image_factory,
    feature_image_factory,
    jacobian_image_factory,
    registered_image_factory,
    segmented_image_factory,
):
    batch: PreprocessingBatch = preprocessing_batch_factory(dataset__owner=user)
    for _ in range(4):
        image = image_factory(dataset=batch.dataset)
        feature_image_factory(source_image=image, preprocessing_batch=batch)
        jacobian_image_factory(source_image=image, preprocessing_batch=batch)
        registered_image_factory(source_image=image, preprocessing_batch=batch)
        segmented_image_factory(source_image=image, preprocessing_batch=batch)

    # Make request and check results
    api_client.force_authenticate(user)
    r = api_client.get(f'/api/v1/preprocessing_batches/{batch.id}/images')
    assert r.status_code == 200
    assert r.json()['count'] == 4
    for entry in r.json()['results']:
        assert 'feature' in entry
        assert 'jacobian' in entry
        assert 'registered' in entry
        assert 'segmented' in entry
        assert entry['dataset'] == batch.dataset.id
