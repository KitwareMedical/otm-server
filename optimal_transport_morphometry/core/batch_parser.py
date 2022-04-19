import csv
from pathlib import Path
from typing import TextIO
from uuid import uuid4

from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import transaction

from optimal_transport_morphometry.core import models

root_dir = Path(__file__).parent.parent.parent
images_dir = root_dir / 'sample_data' / 'images'


@transaction.atomic
def load_batch_from_csv(csvfile: TextIO, dest: models.Dataset) -> models.UploadBatch:
    reader = csv.DictReader(csvfile)
    batch = models.UploadBatch.objects.create(dataset=dest)
    patients = []
    uploads = []
    images = []

    for row in reader:
        expected_name = row.pop('name')
        patient_id = row.pop('ID', '').strip() or uuid4().hex
        # TODO allow using existing patients too
        patient, created = models.Patient.objects.get_or_create(identifier=patient_id)
        if created:
            patients.append(patient)

        # Add uploads
        uploads.append(
            models.PendingUpload(batch=batch, patient=patient, name=expected_name, metadata=row)
        )

        # Add image for corresponding row
        with open(images_dir / expected_name, 'rb') as file_contents:
            images.append(
                models.Image(
                    name=expected_name,
                    dataset=dest,
                    patient=patient,
                    blob=SimpleUploadedFile(name=expected_name, content=file_contents.read()),
                    metadata={'ID': patient_id},
                )
            )

    models.Patient.objects.bulk_create(patients)
    models.PendingUpload.objects.bulk_create(uploads)
    models.Image.objects.bulk_create(images)

    return batch
