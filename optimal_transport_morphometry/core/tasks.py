from tempfile import NamedTemporaryFile

import ants
from celery import shared_task
from django.core.files import File
import numpy as np

from optimal_transport_morphometry.core import models


@shared_task()
def preprocess_images(atlas_id: int, dataset_id: int):
    atlas = models.Atlas.objects.get(pk=atlas_id)
    dataset = models.Dataset.objects.get(pk=dataset_id)

    with NamedTemporaryFile(suffix=atlas.name) as tmp, atlas.blob.open() as blob:
        for chunk in blob.chunks():
            tmp.write(chunk)
        atlas_img = ants.image_read(tmp.name)

    for image in dataset.images:
        with NamedTemporaryFile(suffix=image.name) as tmp, image.blob.open() as blob:
            for chunk in blob.chunks():
                tmp.write(chunk)
            input_img = ants.image_read(tmp.name)

        print(f'Runnning N4 Bias Correction: {image.name}')
        im_n4 = ants.n4_bias_field_correction(input_img)
        print(f'Runnning Registration: {image.name}')
        reg = ants.registration(atlas_img, im_n4)
        jac_img = ants.create_jacobian_determinant_image(atlas_img, reg['fwdtransforms'][0], 1)
        jac_img = jac_img.apply(np.abs)

        reg_model = models.RegisteredImage(source_image=image, atlas=atlas)
        with NamedTemporaryFile(suffix='registered.nii') as tmp:
            ants.image_write(reg['warpedmovout'], tmp.name)
            reg_model.blob = File(tmp, name='registered.nii')
            reg_model.save()

        jac_model = models.JacobianImage(source_image=image, atlas=atlas)
        with NamedTemporaryFile(suffix='jacobian.nii') as tmp:
            ants.image_write(jac_img, tmp.name)
            jac_model.blob = File(tmp, name='jacobian.nii')
            jac_model.save()

    """
    print("Creating Mask")
    priors = [
                ants.image_read( args.atlas_csf ),
                ants.image_read( args.atlas_grey ),
                ants.image_read( args.atlas_white )
            ]
    mask = priors[0].copy()
    mask_view = mask.view()
    for i in range(1, len(priors)):
        mask_view[ priors[i].numpy() > 0 ] = 1
    mask_view[mask_view > 0] = 1
    ants.image_write( mask, "mask.nii")

    print("Runnning Segmentation")
    seg = ants.prior_based_segmentation( im_warped, priors, mask )

    ants.image_write( seg['segmentation'], args.out_segmentation )
    """
