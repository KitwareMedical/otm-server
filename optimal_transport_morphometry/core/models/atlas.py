from __future__ import annotations

from django.db import models
from s3_file_field import S3FileField


class Atlas(models.Model):
    class Meta:
        verbose_name_plural = 'atlases'

    blob = S3FileField()
    name = models.CharField(max_length=255)

    @classmethod
    def default_atlas(cls) -> Atlas:
        return cls.objects.get(name='T1.nii.gz')
