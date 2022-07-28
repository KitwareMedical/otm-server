import pytest

from optimal_transport_morphometry.core.models import Dataset, Image, PendingUpload, UploadBatch


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
def test_image_create_unauthorized(
    api_client, user_factory, s3ff_field_value, pending_upload_factory
):
    # Create a pending upload
    upload: PendingUpload = pending_upload_factory()

    # Make request as user with no access to batch
    api_client.force_authenticate(user_factory())
    r = api_client.post('/api/v1/images', {'pending_upload': upload.pk, 'blob': s3ff_field_value})
    assert r.status_code == 404


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


@pytest.mark.django_db
def test_image_access(
    user,
    api_client,
    dataset_factory,
    image_factory,
):
    # Create dataset with one batch that has one pending upload
    dataset: Dataset = dataset_factory(owner=user)
    image: Image = image_factory(dataset=dataset)

    api_client.force_authenticate(user)
    r = api_client.get(f'/api/v1/images/{image.id}')
    assert r.status_code == 200
    r = api_client.get(f'/api/v1/images/{image.id}/download')
    assert r.status_code == 302


@pytest.mark.django_db
def test_image_access_unauthorized(
    user,
    user_factory,
    api_client,
    dataset_factory,
    image_factory,
):
    # Create dataset with one batch that has one pending upload
    dataset: Dataset = dataset_factory(owner=user)
    image: Image = image_factory(dataset=dataset)

    user2 = user_factory()
    api_client.force_authenticate(user2)
    r = api_client.get(f'/api/v1/images/{image.id}')
    assert r.status_code == 404
    r = api_client.get(f'/api/v1/images/{image.id}/download')
    assert r.status_code == 404
