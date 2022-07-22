import pytest

from optimal_transport_morphometry.core.models import Dataset, PendingUpload, UploadBatch


@pytest.mark.django_db
def test_image_create(
    user,
    api_client,
    s3ff_field_value,
    dataset_factory,
    pending_upload_factory,
    upload_batch_factory,
):
    dataset: Dataset = dataset_factory(owner=user)
    batch: UploadBatch = upload_batch_factory(dataset=dataset)

    # Create two pending uploads
    pending_upload_factory(batch=batch)
    upload: PendingUpload = pending_upload_factory(batch=batch)

    api_client.force_authenticate(user)
    r = api_client.post('/api/v1/images', {'pending_upload': upload.pk, 'blob': s3ff_field_value})
    assert r.status_code == 200

    # Assert batch still exists
    assert UploadBatch.objects.filter(id=batch.id).exists()


@pytest.mark.django_db
def test_image_create_invalid_upload(user, api_client, s3ff_field_value):
    api_client.force_authenticate(user)
    r = api_client.post('/api/v1/images', {'pending_upload': 1, 'blob': s3ff_field_value})
    assert r.status_code == 404


@pytest.mark.django_db
def test_image_create_deletes_batch(
    user,
    api_client,
    s3ff_field_value,
    dataset_factory,
    pending_upload_factory,
    upload_batch_factory,
):
    # Create dataset with one batch that has one pending upload
    dataset: Dataset = dataset_factory(owner=user)
    batch: UploadBatch = upload_batch_factory(dataset=dataset)
    upload: PendingUpload = pending_upload_factory(batch=batch)

    api_client.force_authenticate(user)
    r = api_client.post('/api/v1/images', {'pending_upload': upload.id, 'blob': s3ff_field_value})
    assert r.status_code == 200

    # Assert that the original batch is gone
    assert not UploadBatch.objects.filter(id=batch.id).exists()
