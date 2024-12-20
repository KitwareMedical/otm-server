# Generated by Django 3.2.13 on 2022-07-14 22:08

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0011_alter_dataset_options'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='dataset',
            constraint=models.UniqueConstraint(
                fields=('name', 'owner'), name='unique_owner_dataset_name'
            ),
        ),
    ]
