# Generated by Django 3.2.15 on 2022-08-18 23:51

from django.db import migrations
import s3_file_field.fields


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0017_auto_20220816_2130'),
    ]

    operations = [
        migrations.AddField(
            model_name='dataset',
            name='analysis_result',
            field=s3_file_field.fields.S3FileField(blank=True, null=True),
        ),
    ]
