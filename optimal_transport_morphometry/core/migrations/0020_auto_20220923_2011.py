# Generated by Django 3.2.15 on 2022-09-23 20:11

from django.db import migrations, models
import django.db.models.deletion


def migrate_preprocessing_batches(apps, schema_editor):
    Atlas = apps.get_model('core', 'Atlas')
    default_atlas = Atlas.objects.get(name='T1.nii.gz')

    PreprocessingBatch = apps.get_model('core', 'PreprocessingBatch')
    batches = PreprocessingBatch.objects.filter(atlas_id=1)
    for batch in batches:
        images = [
            im
            for im in (
                batch.core_featureimage.first(),
                batch.core_jacobianimage.first(),
                batch.core_registeredimage.first(),
                batch.core_segmentedimage.first(),
            )
            if im is not None
        ]
        if not images:
            batch.atlas_id = default_atlas.id
        else:
            batch.atlas_id = images[0].atlas_id
        batch.save()


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0019_populate_compressed_atlases'),
    ]

    operations = [
        migrations.AddField(
            model_name='preprocessingbatch',
            name='atlas',
            field=models.ForeignKey(
                default=1,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='preprocessing_batches',
                to='core.atlas',
            ),
            preserve_default=False,
        ),
        # # Copy the atlas entries to the preprocessing batch before removing field from images
        migrations.RunPython(migrate_preprocessing_batches, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name='featureimage',
            name='atlas',
        ),
        migrations.RemoveField(
            model_name='jacobianimage',
            name='atlas',
        ),
        migrations.RemoveField(
            model_name='registeredimage',
            name='atlas',
        ),
        migrations.RemoveField(
            model_name='segmentedimage',
            name='atlas',
        ),
    ]
