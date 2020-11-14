from django.db import models
from django_extensions.db.models import TimeStampedModel


class Dataset(TimeStampedModel, models.Model):
    name = models.CharField(max_length=255, blank=False)
    description = models.TextField(default='', max_length=3000)
