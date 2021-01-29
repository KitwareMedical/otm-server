from tempfile import NamedTemporaryFile

import ants
from celery import shared_task
from django.core.files import File
from django.db import transaction
import numpy as np

from optimal_transport_morphometry.core import models


@shared_task()
def preprocess_images(
    atlas_id: int, atlas_csf_id: int, atlas_grey_id: int, atlas_white_id: int, dataset_id: int,
    replace: bool = False
):
    atlas = models.Atlas.objects.get(pk=atlas_id)
    atlas_csf = models.Atlas.objects.get(pk=atlas_csf_id)
    atlas_grey = models.Atlas.objects.get(pk=atlas_grey_id)
    atlas_white = models.Atlas.objects.get(pk=atlas_white_id)
    dataset = models.Dataset.objects.get(pk=dataset_id)

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

        print(f'Runnning N4 bias correction: {image.name}')
        im_n4 = ants.n4_bias_field_correction(input_img)
        del input_img
        print(f'Runnning registration: {image.name}')
        reg = ants.registration(atlas_img, im_n4)
        del im_n4
        jac_img = ants.create_jacobian_determinant_image(atlas_img, reg['fwdtransforms'][0], 1)
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
        del jac_img

        print(f'Runnning segmentation: {image.name}')
        seg = ants.prior_based_segmentation(reg_img, priors, mask)
        del reg_img

        seg_model = models.SegmentedImage(source_image=image, atlas=atlas)
        with NamedTemporaryFile(suffix='segmented.nii') as tmp:
            ants.image_write(seg['segmentation'], tmp.name)
            del seg
            seg_model.blob = File(tmp, name='segmented.nii')
            seg_model.save()


@transaction.atomic
def _delete_preprocessing_artifacts(image: models.Image) -> None:
    for model in [models.JacobianImage, models.SegmentedImage, models.RegisteredImage]:
        model.objects.filter(source_image=image).delete()


def _already_preprocessed(image: models.Image) -> bool:
    return all(
        model.objects.filter(source_image=image).count() > 0
        for model in [models.JacobianImage, models.SegmentedImage, models.RegisteredImage]
    )
