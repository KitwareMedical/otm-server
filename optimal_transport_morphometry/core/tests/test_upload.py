from pathlib import Path

import pytest

from optimal_transport_morphometry.core import batch_parser, models


@pytest.fixture
def batch(dataset) -> models.UploadBatch:
    csvfile = Path(__file__).parent / 'test.csv'
    with open(csvfile, 'r', newline='') as fd:
        return batch_parser.load_batch_from_csv(fd, dataset)


@pytest.mark.django_db
def test_load_batch_from_csv(batch):
    assert batch.pending_uploads.count() == 3
    assert models.Patient.objects.count() == 3


@pytest.mark.django_db
def test_upload_batch_finalization_cleanup(batch):
    for pending in batch.pending_uploads.all():
        batch.refresh_from_db()
        pending.delete()

    with pytest.raises(models.UploadBatch.DoesNotExist):
        batch.refresh_from_db()
