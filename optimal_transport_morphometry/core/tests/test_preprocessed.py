import pytest

from optimal_transport_morphometry.core.models import Dataset


@pytest.mark.django_db
def test_fetch_preprocessed_images(
    user,
    api_client,
    dataset_factory,
    image_factory,
    feature_image_factory,
    jacobian_image_factory,
    registered_image_factory,
    segmented_image_factory,
):
    dataset: Dataset = dataset_factory(owner=user)
    for _ in range(4):
        image = image_factory(dataset=dataset)
        feature_image_factory(source_image=image)
        jacobian_image_factory(source_image=image)
        registered_image_factory(source_image=image)
        segmented_image_factory(source_image=image)

    # Make request and check results
    api_client.force_authenticate(user)
    r = api_client.get(f'/api/v1/datasets/{dataset.id}/preprocessed_images')

    assert r.json()['count'] == 4
    for entry in r.json()['results']:
        assert 'feature' in entry
        assert 'jacobian' in entry
        assert 'registered' in entry
        assert 'segmented' in entry
        assert entry['dataset'] == dataset.id
