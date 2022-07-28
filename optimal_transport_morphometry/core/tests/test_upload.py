import pathlib
from pathlib import Path
from typing import List

# from django.core.files import File
# from django.core.files.uploadedfile import SimpleUploadedFile
import pytest

from optimal_transport_morphometry.core import batch_parser, models

# from optimal_transport_morphometry.core.models.dataset import Dataset

testcsv = pathlib.Path(__file__).parent / 'test.csv'


@pytest.fixture
def batch(dataset) -> models.UploadBatch:
    csvfile = Path(__file__).parent / 'test.csv'
    with open(csvfile, 'r', newline='') as fd:
        return batch_parser.load_batch_from_csv(fd, dataset)


@pytest.mark.django_db
def test_load_batch_from_csv(batch):
    assert batch.pending_uploads.count() == 3


@pytest.mark.django_db
def test_upload_batch_finalization_cleanup(batch):
    for pending in batch.pending_uploads.all():
        batch.refresh_from_db()
        pending.delete()

    with pytest.raises(models.UploadBatch.DoesNotExist):
        batch.refresh_from_db()


@pytest.mark.django_db
def test_upload_batch_access(api_client, user, dataset_factory, upload_batch_factory):
    batch: models.UploadBatch = upload_batch_factory(dataset=dataset_factory(owner=user))

    api_client.force_authenticate(user)
    r = api_client.get(f'/api/v1/upload/batches/{batch.id}')
    assert r.status_code == 200


@pytest.mark.django_db
def test_upload_batch_access_unauthorized(
    api_client, user, user_factory, dataset_factory, upload_batch_factory
):
    batch: models.UploadBatch = upload_batch_factory(dataset=dataset_factory(owner=user))

    api_client.force_authenticate(user_factory())
    r = api_client.get(f'/api/v1/upload/batches/{batch.id}')
    assert r.status_code == 404


@pytest.mark.django_db
def test_upload_batch_pending_access(
    api_client, user, dataset_factory, upload_batch_factory, pending_upload_factory
):
    dataset: models.Dataset = dataset_factory(owner=user)
    batch: models.UploadBatch = upload_batch_factory(dataset=dataset)
    uploads: List[models.PendingUpload] = [pending_upload_factory(batch=batch) for _ in range(10)]

    api_client.force_authenticate(user)
    r = api_client.get(f'/api/v1/upload/batches/{batch.id}/pending')
    assert r.status_code == 200
    assert len(r.json()['results']) == len(uploads)


@pytest.mark.django_db
def test_upload_batch_pending_access_unauthorized(
    api_client, user, dataset_factory, upload_batch_factory, pending_upload_factory
):
    dataset: models.Dataset = dataset_factory()
    batch: models.UploadBatch = upload_batch_factory(dataset=dataset)

    # Create pending uploads
    for _ in range(10):
        pending_upload_factory(batch=batch)

    # Assert no authorization
    api_client.force_authenticate(user)
    r = api_client.get(f'/api/v1/upload/batches/{batch.id}/pending')
    assert r.status_code == 404


@pytest.mark.django_db
def test_pending_upload_access(api_client, user, dataset_factory, pending_upload_factory):
    dataset: models.Dataset = dataset_factory(owner=user)
    upload: models.PendingUpload = pending_upload_factory(batch__dataset=dataset)

    # Assert no authorization
    api_client.force_authenticate(user)
    r = api_client.get(f'/api/v1/upload/pending/{upload.id}')
    assert r.status_code == 200


@pytest.mark.django_db
def test_pending_upload_access_unauthorized(
    api_client, user, dataset_factory, pending_upload_factory
):
    dataset: models.Dataset = dataset_factory()
    upload: models.PendingUpload = pending_upload_factory(batch__dataset=dataset)

    # Assert no authorization
    api_client.force_authenticate(user)
    r = api_client.get(f'/api/v1/upload/pending/{upload.id}')
    assert r.status_code == 404


# TODO: Add test for creating upload batch
# @pytest.mark.django_db
# def test_rest_create_upload_batch(api_client, user, dataset_factory):
#     file = SimpleUploadedFile(
#         'test.csv',
#         File(open(testcsv, 'rb')).read(),
#         content_type='multipart/form-data',
#         # content_type='text/csv',
#     )

#     dataset: Dataset = dataset_factory(owner=user)
#     r = api_client.post(
#         '/api/v1/upload_batches',
#         {
#             'csvfile': file,
#             'dataset': dataset.id,
#         },
#         # content_type='multipart/form-data',
#         content_disposition="attachment; filename=test.csv",
#     )
#     print(r.json())
#     assert r.status_code == 201
