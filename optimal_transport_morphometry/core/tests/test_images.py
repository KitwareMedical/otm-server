import pytest

from optimal_transport_morphometry.core.models import Dataset, PendingUpload, UploadBatch


@pytest.mark.django_db
def test_image_create(
    user,
    api_client,
    dataset_factory,
    s3ff_field_value,
    pending_upload_factory,
    upload_batch_factory,
):
    dataset: Dataset = dataset_factory(owner=user)
    batch: UploadBatch = upload_batch_factory(dataset=dataset)
    upload: PendingUpload = pending_upload_factory(batch=batch)

    api_client.force_authenticate(user)
    r = api_client.post('/api/v1/images', {'pending_upload': upload.pk, 'blob': s3ff_field_value})
    assert r.status_code == 200


@pytest.mark.django_db
def test_image_create_invalid_upload(user, api_client, s3ff_field_value):
    api_client.force_authenticate(user)
    r = api_client.post('/api/v1/images', {'pending_upload': 1, 'blob': s3ff_field_value})
    assert r.status_code == 404
