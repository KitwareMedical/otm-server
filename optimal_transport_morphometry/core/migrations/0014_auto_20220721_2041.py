# Generated by Django 3.2.13 on 2022-07-21 20:41

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0013_auto_20220720_1828'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='image',
            name='patient',
        ),
        migrations.RemoveField(
            model_name='pendingupload',
            name='patient',
        ),
    ]
