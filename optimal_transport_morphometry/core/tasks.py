import csv
import os
import shutil
import subprocess
from tempfile import NamedTemporaryFile, TemporaryDirectory
from typing import List, TextIO

from celery import shared_task
from django.core.files import File

from optimal_transport_morphometry.core import models


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
    atlas = models.Atlas.objects.get(name='T1.nii')
    atlas_csf = models.Atlas.objects.get(name='csf.nii')
    atlas_grey = models.Atlas.objects.get(name='grey.nii')
    atlas_white = models.Atlas.objects.get(name='white.nii')

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
    with NamedTemporaryFile(suffix='atlas.nii') as tmp, atlas.blob.open() as blob:
        for chunk in blob.chunks():
            tmp.write(chunk)
        atlas_img = ants.image_read(tmp.name)

    with NamedTemporaryFile(suffix='atlas_csf.nii') as tmp, atlas_csf.blob.open() as blob:
        for chunk in blob.chunks():
            tmp.write(chunk)
        atlas_csf_img = ants.image_read(tmp.name)

    with NamedTemporaryFile(suffix='atlas_grey.nii') as tmp, atlas_grey.blob.open() as blob:
        for chunk in blob.chunks():
            tmp.write(chunk)
        atlas_grey_img = ants.image_read(tmp.name)

    with NamedTemporaryFile(suffix='atlas_white.nii') as tmp, atlas_white.blob.open() as blob:
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
        common_model_args = {'source_image': image, 'preprocessing_batch': batch, 'atlas': atlas}

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

        feature_model = models.FeatureImage(
            **common_model_args, metadata={'downsample_factor': downsample}
        )
        with NamedTemporaryFile(suffix='feature.nii.gz') as tmp:
            ants.image_write(feature_img, tmp.name)
            feature_model.blob = File(tmp, name='feature.nii.gz')
            feature_model.save()

    # Update batch status
    batch.status = models.PreprocessingBatch.Status.FINISHED
    batch.save()


@shared_task()
def run_utm(dataset_id: int):
    # using default_configuration.yml in UTM repo for now
    # TODO: load config.yml file as well

    dataset: models.Dataset = models.Dataset.objects.get(pk=dataset_id)
    output_folder = f'/srv/shiny-server/utm_{dataset_id}'  # shiny-server directory
    utm_folder = '/opt/UTM'

    # Set status before starting
    dataset.analysis_status = models.Dataset.ProcessStatus.RUNNING
    dataset.save(update_fields=['analysis_status'])

    with TemporaryDirectory() as tmpdir:
        variables = []
        for image in dataset.images.all():
            meta = image.metadata
            meta.setdefault('name', image.name)
            variables.append(meta)

            feature_image = image.feature_images.first()
            filename = f'{tmpdir}/{meta["name"]}'
            with feature_image.blob.open() as blob, open(filename, 'wb') as fd:
                for chunk in blob.chunks():
                    fd.write(chunk)

        variables_filename = f'{tmpdir}/variables.csv'
        headers = variables[0].keys()
        with open(variables_filename, 'w') as csvfile:
            _write_csv(csvfile, headers, variables)

        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        # copy necessary R shiny files
        shutil.copyfile(f'{utm_folder}/Scripts/Shiny/app.R', f'{output_folder}/app.R')
        shutil.copyfile(
            f'{utm_folder}/Scripts/Shiny/shiny-help.md', f'{output_folder}/shiny-help.md'
        )
        shutil.copyfile(
            f'{utm_folder}/Scripts/ShinyVtkScripts/render.js', f'{output_folder}/render.js'
        )

        result = subprocess.run(
            [
                'Rscript',
                '/opt/UTM/Scripts/run.utm.barycenter.R',
                tmpdir,
                variables_filename,
                '--working.folder',
                output_folder,
            ]
        )
        if result.returncode == 0:
            dataset.analysis_status = models.Dataset.ProcessStatus.FINISHED
        else:
            dataset.analysis_status = models.Dataset.ProcessStatus.FAILED

        # Save
        dataset.save(update_fields=['analysis_status'])


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
