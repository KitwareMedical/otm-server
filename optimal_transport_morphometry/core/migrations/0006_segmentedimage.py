# Generated by Django 3.1.5 on 2021-01-23 15:52

from django.db import migrations, models
import django.db.models.deletion
import s3_file_field.fields


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0005_jacobianimage_registeredimage'),
    ]

    operations = [
        migrations.CreateModel(
            name='SegmentedImage',
            fields=[
                (
                    'id',
                    models.AutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name='ID'
                    ),
                ),
                (
                    'blob',
                    s3_file_field.fields.S3FileField(
                        max_length=2000,
                        upload_to=s3_file_field.fields.S3FileField.uuid_prefix_filename,
                    ),
                ),
                (
                    'atlas',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name='segmented_images',
                        to='core.atlas',
                    ),
                ),
                (
                    'source_image',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='segmented_images',
                        to='core.image',
                    ),
                ),
            ],
        ),
    ]
