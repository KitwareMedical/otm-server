from pathlib import Path
from typing import List, Optional, TextIO

from click import ClickException
from django.contrib.auth.models import User
from django.core.files import File
from django.core.files.uploadedfile import SimpleUploadedFile
import djclick as click

from optimal_transport_morphometry.core.batch_parser import load_batch_from_csv
from optimal_transport_morphometry.core.models import (
    Atlas,
    Dataset,
    Image,
    PendingUpload,
    UploadBatch,
)

root_dir = Path(__file__).parents[4]
images_dir = root_dir / 'sample_data' / 'images'


@click.command()
@click.argument('csv', type=click.File())
@click.option('--owner', 'email', required=True, help='The email of the dataset owner.')
@click.option('--dataset-name', default='Test dataset', help='The name of the dataset to create.')
@click.option('--clear', is_flag=True, help='Clear all existing upload batches.')
@click.option('--include-images', is_flag=True, help='Include upload of corresponding images.')
def command(csv: TextIO, email: str, dataset_name: str, clear: bool, include_images: bool) -> None:
    owner: Optional[User] = User.objects.filter(email=email).first()
    if owner is None:
        raise ClickException(f'Owner not found with email: {owner}')

    for name in ['grey', 'white', 'csf', 'T1']:
        if not Atlas.objects.filter(name=f'{name}.nii.gz').exists():
            print(f'Uploading {name} atlas')
            with open(f'sample_data/atlases/{name}.nii.gz', 'rb') as fd:
                Atlas.objects.create(name=f'{name}.nii.gz', blob=File(fd, name=f'{name}.nii.gz'))

    if clear:
        print('Deleting all upload batches')
        UploadBatch.objects.all().delete()

    # Add dataset and pending upload batch
    print('Ingesting upload batch and pending upload...')
    dataset, _ = Dataset.objects.get_or_create(name=dataset_name, owner=owner)
    batch = load_batch_from_csv(csv, dataset=dataset)

    # Automatically ingest images if desired
    if include_images:
        print('Uploading corresponding images...')
        uploads: List[PendingUpload] = list(batch.pending_uploads.all())
        images: List[Image] = []
        for upload in uploads:
            with open(images_dir / upload.name, 'rb') as file_contents:
                images.append(
                    Image(
                        name=upload.name,
                        dataset=batch.dataset,
                        metadata=upload.metadata,
                        blob=SimpleUploadedFile(name=upload.name, content=file_contents.read()),
                    )
                )

        # Create all at once
        Image.objects.bulk_create(images)
