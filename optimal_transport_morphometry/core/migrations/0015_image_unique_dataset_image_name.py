# Generated by Django 3.2.15 on 2022-08-11 19:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0015_auto_20220812_1756'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='image',
            constraint=models.UniqueConstraint(
                fields=('dataset', 'name'), name='unique_dataset_image_name'
            ),
        ),
    ]
