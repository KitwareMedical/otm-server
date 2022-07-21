import pathlib
from pathlib import Path

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


# TODO: Add test for upload batch permissions
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
