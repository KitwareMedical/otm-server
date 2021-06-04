from typing import TextIO

from django.core.files import File
import djclick as click

from optimal_transport_morphometry.core.batch_parser import load_batch_from_csv
from optimal_transport_morphometry.core.models import Atlas, Dataset, UploadBatch


@click.command()
@click.argument('csv', type=click.File())
@click.option('--dataset-name', default='Test dataset')
@click.option('--clear', is_flag=True)
def command(csv: TextIO, dataset_name: str, clear: bool) -> None:
    for name in ['grey', 'white', 'csf', 'T1']:
        if not Atlas.objects.filter(name=f'{name}.nii').exists():
            print(f'Uploading {name} atlas')
            with open(f'sample_data/atlases/{name}.nii', 'rb') as fd:
                Atlas.objects.create(name=f'{name}.nii', blob=File(fd, name=f'{name}.nii'))

    if clear:
        print('Deleting all upload batches')
        UploadBatch.objects.all().delete()

    # Add dataset and pending upload batch
    dataset, _ = Dataset.objects.get_or_create(name=dataset_name)
    load_batch_from_csv(csv, dest=dataset)
