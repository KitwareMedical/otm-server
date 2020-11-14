from django.db import models
from s3_file_field import S3FileField


class Atlas(models.Model):
    blob = S3FileField()
    name = models.CharField(max_length=255)
