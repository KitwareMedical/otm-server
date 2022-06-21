from django.contrib.auth.models import User
from django.db import models
from django_extensions.db.models import TimeStampedModel


class Dataset(TimeStampedModel, models.Model):
    name = models.CharField(max_length=255, blank=False)
    description = models.TextField(default='', blank=True, max_length=3000)
    preprocessing_complete = models.BooleanField(default=False)
    analysis_complete = models.BooleanField(default=False)
    public = models.BooleanField(default=False)
    owner = models.ForeignKey(User, related_name='datasets_owned', on_delete=models.CASCADE)

    class Meta:
        permissions = (('collaborator', 'Collaborator'),)
