from typing import TextIO

import djclick as click

from optimal_transport_morphometry.core.batch_parser import load_batch_from_csv
from optimal_transport_morphometry.core.models import Dataset


@click.command()
@click.argument('csv', type=click.File())
@click.option('--dataset-name', default='Test dataset')
def command(csv: TextIO, dataset_name: str) -> None:
    dataset, _ = Dataset.objects.get_or_create(name=dataset_name)
    load_batch_from_csv(csv, dest=dataset)
