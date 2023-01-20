import tempfile
from typing import Optional
import zipfile

from click import ClickException
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
import djclick as click

from optimal_transport_morphometry.core.models import (
    AnalysisResult,
    Atlas,
    Dataset,
    PreprocessingBatch,
)
from optimal_transport_morphometry.core.tasks import upload_analysis_images


@click.command()
@click.argument('zip_filename', type=click.Path())
@click.option('--owner', 'email', required=True, help='The email of the dataset owner.')
@click.option('--dataset-name', default='Test dataset', help='The name of the dataset to create.')
def command(zip_filename: click.Path, email: str, dataset_name: str) -> None:
    owner: Optional[User] = User.objects.filter(email=email).first()
    if owner is None:
        raise ClickException(f'Owner not found with email: {owner}')

    # Create dataset
    # SimpleUploadedFile(name=upload.name, content=file_contents.read())
    dataset, _ = Dataset.objects.get_or_create(name=dataset_name, owner=owner)
    batch, _ = PreprocessingBatch.objects.get_or_create(
        dataset=dataset,
        status=PreprocessingBatch.Status.FINISHED,
        atlas=Atlas.objects.get(name='T1.nii.gz'),
    )

    # Create analysis
    analysis = AnalysisResult.objects.create(
        preprocessing_batch=batch, status=AnalysisResult.Status.PENDING
    )

    # Set current preprocessing batch and analysis result
    dataset.current_preprocessing_batch = batch
    dataset.current_analysis_result = analysis
    dataset.save()

    # Zip file
    with open(zip_filename, 'rb') as f:
        analysis.zip_file = SimpleUploadedFile(
            name=f'dataset_{dataset.id}_utm_analysis_{analysis.id}.zip', content=f.read()
        )
        analysis.save()

    # Extract zip file and set data
    with tempfile.TemporaryDirectory() as tempdir:
        with zipfile.ZipFile(zip_filename, 'r') as zip_ref:
            zip_ref.extractall(tempdir)

        analysis.data = upload_analysis_images(tempdir)
        analysis.status = AnalysisResult.Status.FINISHED
        analysis.save()
