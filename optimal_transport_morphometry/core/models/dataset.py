from django.db import models
from django_extensions.db.models import TimeStampedModel


class Dataset(TimeStampedModel, models.Model):
    name = models.CharField(max_length=255, blank=False)
    description = models.TextField(default='', blank=True, max_length=3000)
    preprocessing_complete = models.BooleanField(default=False)
    analysis_complete = models.BooleanField(default=False)
