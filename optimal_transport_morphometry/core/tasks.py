import csv
import os
import shutil
import subprocess
from tempfile import NamedTemporaryFile, TemporaryDirectory
from typing import List, TextIO

from celery import shared_task
from django.core.files import File
from django.db import transaction

from optimal_transport_morphometry.core import models


@shared_task()
def preprocess_images(dataset_id: int, replace: bool = False, downsample: float = 3.0):
    # Import to avoid need for ants package in API
    import ants
    import numpy as np

    atlas = models.Atlas.objects.filter(name='T1.nii').first()
    atlas_csf = models.Atlas.objects.filter(name='csf.nii').first()
    atlas_grey = models.Atlas.objects.filter(name='grey.nii').first()
    atlas_white = models.Atlas.objects.filter(name='white.nii').first()
    dataset: models.Dataset = models.Dataset.objects.get(pk=dataset_id)

    # Check that all atlases found
    if None in [atlas, atlas_csf, atlas_grey, atlas_white]:
        raise Exception('Not all atlases found')

    # Ensure in running state
    if dataset.preprocessing_status != models.Dataset.ProcessStatus.RUNNING:
        dataset.preprocessing_status = models.Dataset.ProcessStatus.RUNNING
        dataset.save(update_fields=['preprocessing_status'])

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

    for image in dataset.images.all():
        if replace:
            _delete_preprocessing_artifacts(image)
        elif _already_preprocessed(image):
            continue
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

        reg_model = models.RegisteredImage(source_image=image, atlas=atlas)
        reg_img = reg['warpedmovout']
        with NamedTemporaryFile(suffix='registered.nii') as tmp:
            ants.image_write(reg_img, tmp.name)
            reg_model.blob = File(tmp, name='registered.nii')
            reg_model.save()

        jac_model = models.JacobianImage(source_image=image, atlas=atlas)
        with NamedTemporaryFile(suffix='jacobian.nii') as tmp:
            ants.image_write(jac_img, tmp.name)
            jac_model.blob = File(tmp, name='jacobian.nii')
            jac_model.save()

        print(f'Running segmentation: {image.name}')
        seg = ants.prior_based_segmentation(reg_img, priors, mask)
        del reg_img

        seg_model = models.SegmentedImage(source_image=image, atlas=atlas)
        with NamedTemporaryFile(suffix='segmented.nii') as tmp:
            ants.image_write(seg['segmentation'], tmp.name)
            seg_model.blob = File(tmp, name='segmented.nii')
            seg_model.save()

        print(f'Creating feature image: {image.name}')
        seg_img_view = seg['segmentation'].view()
        feature_img = seg['segmentation'].copy()
        feature_img_view = feature_img.view()
        feature_img_view.fill(0)
        feature_img_view[seg_img_view == 3] = 1  # 3 is white matter label

        intensity_img_view = jac_img.view()
        feature_img_view *= intensity_img_view

        if downsample > 1:
            shape = np.round(np.asarray(feature_img.shape) / downsample)
            feature_img = ants.resample_image(feature_img, shape, True)

        feature_model = models.FeatureImage(
            source_image=image, atlas=atlas, downsample_factor=downsample
        )
        with NamedTemporaryFile(suffix='feature.nii') as tmp:
            ants.image_write(feature_img, tmp.name)
            feature_model.blob = File(tmp, name='feature.nii')
            feature_model.save()

    dataset.preprocessing_status = models.Dataset.ProcessStatus.FINISHED
    dataset.save()


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


@transaction.atomic
def _delete_preprocessing_artifacts(image: models.Image) -> None:
    for model in [
        models.JacobianImage,
        models.SegmentedImage,
        models.RegisteredImage,
        models.FeatureImage,
    ]:
        model.objects.filter(source_image=image).delete()  # type: ignore


def _already_preprocessed(image: models.Image) -> bool:
    return all(
        model.objects.filter(source_image=image).count() > 0  # type: ignore
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
