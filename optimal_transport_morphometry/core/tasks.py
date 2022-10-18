import csv
import pathlib
import shutil
import subprocess
import tempfile
from tempfile import NamedTemporaryFile, TemporaryDirectory, mkdtemp
from typing import List, TextIO

from celery import shared_task
from django.core.files import File
from django.core.files.uploadedfile import SimpleUploadedFile

from optimal_transport_morphometry.core import models
from optimal_transport_morphometry.core.storage import upload_local_file

UTM_FOLDER = '/opt/UTM'


def handle_preprocess_failure(self, exc, task_id, args, kwargs, einfo):
    batch_id = args[0]
    batch: models.PreprocessingBatch = models.PreprocessingBatch.objects.select_related(
        'dataset'
    ).get(pk=batch_id)

    # Set fields and save
    batch.error_message += str(exc) + '\n\n' + str(einfo)
    batch.status = models.PreprocessingBatch.Status.FAILED
    batch.save(update_fields=['error_message', 'status'])


@shared_task(on_failure=handle_preprocess_failure)
def preprocess_images(batch_id: int, downsample: float = 3.0):
    # Import to avoid need for ants package in API
    import ants
    import numpy as np

    # Fetch atlases, raising an error if some aren't found
    atlas = models.Atlas.objects.get(name='T1.nii.gz')
    atlas_csf = models.Atlas.objects.get(name='csf.nii.gz')
    atlas_grey = models.Atlas.objects.get(name='grey.nii.gz')
    atlas_white = models.Atlas.objects.get(name='white.nii.gz')

    # Fetch dataset
    batch: models.PreprocessingBatch = models.PreprocessingBatch.objects.select_related(
        'dataset'
    ).get(pk=batch_id)
    dataset: models.Dataset = batch.dataset

    # Ensure in running state
    if batch.status != models.PreprocessingBatch.Status.RUNNING:
        batch.status = models.PreprocessingBatch.Status.RUNNING
        batch.save(update_fields=['status'])

    print('Downloading atlas files')
    with NamedTemporaryFile(suffix='atlas.nii.gz') as tmp, atlas.blob.open() as blob:
        for chunk in blob.chunks():
            tmp.write(chunk)
        atlas_img = ants.image_read(tmp.name)

    with NamedTemporaryFile(suffix='atlas_csf.nii.gz') as tmp, atlas_csf.blob.open() as blob:
        for chunk in blob.chunks():
            tmp.write(chunk)
        atlas_csf_img = ants.image_read(tmp.name)

    with NamedTemporaryFile(suffix='atlas_grey.nii.gz') as tmp, atlas_grey.blob.open() as blob:
        for chunk in blob.chunks():
            tmp.write(chunk)
        atlas_grey_img = ants.image_read(tmp.name)

    with NamedTemporaryFile(suffix='atlas_white.nii.gz') as tmp, atlas_white.blob.open() as blob:
        for chunk in blob.chunks():
            tmp.write(chunk)
        atlas_white_img = ants.image_read(tmp.name)

    print('Creating mask')
    priors = [atlas_csf_img, atlas_grey_img, atlas_white_img]
    mask = priors[0].copy()
    mask_view = mask.view()
    for i in range(1, len(priors)):
        mask_view[priors[i].numpy() > 0] = 1
    mask_view[mask_view > 0] = 1

    for image in dataset.images.order_by('name').all():
        # Options that will be shared among each created model
        common_model_args = {'source_image': image, 'preprocessing_batch': batch}

        # Check if image already processed
        if _already_preprocessed(image, batch_id):
            continue

        # Read img
        with NamedTemporaryFile(suffix=image.name) as tmp, image.blob.open() as blob:
            for chunk in blob.chunks():
                tmp.write(chunk)
            input_img = ants.image_read(tmp.name)

        print(f'Running N4 bias correction: {image.name}')
        im_n4 = ants.n4_bias_field_correction(input_img)
        del input_img
        print(f'Running registration: {image.name}')
        reg = ants.registration(atlas_img, im_n4)
        del im_n4
        jac_img = ants.create_jacobian_determinant_image(
            atlas_img, reg['fwdtransforms'][0], False, True
        )
        jac_img = jac_img.apply(np.abs)

        reg_model = models.RegisteredImage(**common_model_args)
        reg_img = reg['warpedmovout']
        with NamedTemporaryFile(suffix='registered.nii.gz') as tmp:
            ants.image_write(reg_img, tmp.name)
            reg_model.blob = File(tmp, name='registered.nii.gz')
            reg_model.save()

        jac_model = models.JacobianImage(**common_model_args)
        with NamedTemporaryFile(suffix='jacobian.nii.gz') as tmp:
            ants.image_write(jac_img, tmp.name)
            jac_model.blob = File(tmp, name='jacobian.nii.gz')
            jac_model.save()

        print(f'Running segmentation: {image.name}')
        seg = ants.prior_based_segmentation(reg_img, priors, mask)
        del reg_img

        seg_model = models.SegmentedImage(**common_model_args)
        with NamedTemporaryFile(suffix='segmented.nii.gz') as tmp:
            ants.image_write(seg['segmentation'], tmp.name)
            seg_model.blob = File(tmp, name='segmented.nii.gz')
            seg_model.save()

        print(f'Creating feature image: {image.name}')
        seg_img_view = seg['segmentation'].view()
        feature_img = seg['segmentation'].copy()
        feature_img_view = feature_img.view()
        feature_img_view.fill(0)
        feature_img_view[seg_img_view == 2] = 1  # 2 is grey matter label, 3 is white matter label

        intensity_img_view = jac_img.view()
        feature_img_view *= intensity_img_view

        if downsample > 1:
            shape = np.round(np.asarray(feature_img.shape) / downsample)
            feature_img = ants.resample_image(feature_img, shape, True)

        feature_model = models.FeatureImage(**common_model_args, downsample_factor=downsample)
        with NamedTemporaryFile(suffix='feature.nii.gz') as tmp:
            ants.image_write(feature_img, tmp.name)
            feature_model.blob = File(tmp, name='feature.nii.gz')
            feature_model.save()

    # Update batch status
    batch.status = models.PreprocessingBatch.Status.FINISHED
    batch.save()


def upload_analysis_images(output_dir: str):
    features = ['allocation', 'transport', 'vbm']
    data = {}

    def handle_path(path: pathlib.Path):
        # Ignore files at this level
        if path.is_file():
            return

        path_data = {}
        for feature in features:
            # If any of these features don't exist, return
            feature_path = path / feature
            if not feature_path.exists():
                return

            # If either image aren't found, return
            correlation = feature_path / 'correlation.nii.gz'
            pvalue = feature_path / 'pvalue.nii.gz'
            if not (correlation.exists() and pvalue.exists()):
                return

            # Perform upload
            path_data[feature] = {
                'correlation': upload_local_file(str(correlation)),
                'pvalue': upload_local_file(str(pvalue)),
            }

        # Loop finished, all feature images uploaded, add to data dict
        data[path.name] = path_data

    image_dir = pathlib.Path(output_dir) / 'Analysis' / 'Images'
    for variable_path in image_dir.iterdir():
        handle_path(variable_path)

    return data


def handle_analysis_failure(self, exc, task_id, args, kwargs, einfo):
    analysis_id = args[0]
    analysis_result: models.AnalysisResult = models.AnalysisResult.objects.get(id=analysis_id)

    # Set fields and save
    analysis_result.error_message += str(exc) + '\n\n' + str(einfo)
    analysis_result.status = models.PreprocessingBatch.Status.FAILED
    analysis_result.save(update_fields=['error_message', 'status'])


@shared_task(on_failure=handle_analysis_failure)
def run_utm(analysis_id: int):
    # using default_configuration.yml in UTM repo for now
    # TODO: load config.yml file as well
    analysis_result: models.AnalysisResult = models.AnalysisResult.objects.select_related(
        'preprocessing_batch__dataset'
    ).get(id=analysis_id)
    preprocessing_batch: models.PreprocessingBatch = analysis_result.preprocessing_batch
    dataset: models.Dataset = preprocessing_batch.dataset

    # Set status before starting
    analysis_result.status = models.AnalysisResult.Status.RUNNING
    analysis_result.save()

    # TODO: Since analysis isn't being visualized by R shiny, output all
    # data into a temporary folder, to be removed after the task completes
    with TemporaryDirectory() as tmpdir:
        # Since these folders are contained within tmpdir,
        # they will be automatically deleted when tmpdir is deleted
        input_folder = mkdtemp(dir=tmpdir)
        output_folder = mkdtemp(dir=tmpdir)

        # Get all feature images in this preprocessing batch
        feature_image_qs = models.FeatureImage.objects.filter(
            preprocessing_batch=preprocessing_batch
        ).select_related('source_image')

        # Iterate over every feature image
        variables = []
        for feature_image in feature_image_qs:
            image = feature_image.source_image
            meta = image.metadata
            meta.setdefault('name', image.name)

            # Ensure file has .nii.gz extension
            # Ants will produce a segmentation fault if it tries to read a
            # compressed image with an uncompressed file extension, and visa versa
            meta['name'] = pathlib.Path(meta['name']).with_suffix('.nii.gz')

            # Add meta to variables
            variables.append(meta)

            # Write feature image to file
            filename = f'{input_folder}/{meta["name"]}'
            with feature_image.blob.open() as blob, open(filename, 'wb') as fd:
                for chunk in blob.chunks():
                    fd.write(chunk)

        # Write variables to a csv file
        variables_filename = f'{input_folder}/variables.csv'
        headers = variables[0].keys()
        with open(variables_filename, 'w') as csvfile:
            _write_csv(csvfile, headers, variables)

        # copy necessary R shiny files
        shutil.copyfile(f'{UTM_FOLDER}/Scripts/Shiny/app.R', f'{output_folder}/app.R')
        shutil.copyfile(
            f'{UTM_FOLDER}/Scripts/Shiny/shiny-help.md', f'{output_folder}/shiny-help.md'
        )
        shutil.copyfile(
            f'{UTM_FOLDER}/Scripts/ShinyVtkScripts/render.js', f'{output_folder}/render.js'
        )

        result = subprocess.run(
            [
                'Rscript',
                '/opt/UTM/Scripts/run.utm.barycenter.R',
                input_folder,
                variables_filename,
                '--working.folder',
                output_folder,
            ]
        )

        # Set analysis status and return if failed
        analysis_result.status = (
            models.AnalysisResult.Status.FINISHED
            if result.returncode == 0
            else models.AnalysisResult.Status.FAILED
        )

        # Create and upload zip file
        if analysis_result.status == models.AnalysisResult.Status.FINISHED:
            # Create zip
            zip_filename = shutil.make_archive(
                tempfile.mktemp(), 'zip', root_dir=output_folder, base_dir='./'
            )
            with open(zip_filename, 'rb') as f:
                analysis_result.zip_file = SimpleUploadedFile(
                    name=f'dataset_{dataset.id}_utm_analysis_{analysis_result.id}.zip',
                    content=f.read(),
                )

            # Upload images to S3
            analysis_result.data = upload_analysis_images(output_folder)

        # Save
        analysis_result.save()
        dataset.save()


def _already_preprocessed(image: models.Image, batch_id: int) -> bool:
    return all(
        model.objects.filter(source_image=image, preprocessing_batch=batch_id).count() > 0
        for model in [
            models.JacobianImage,
            models.SegmentedImage,
            models.RegisteredImage,
            models.FeatureImage,
        ]
    )


def _write_csv(csvfile: TextIO, headers: List[str], rows: List[dict]):
    writer = csv.DictWriter(csvfile, fieldnames=headers)
    writer.writeheader()
    writer.writerows(rows)
