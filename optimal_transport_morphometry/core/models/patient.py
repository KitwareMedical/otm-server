from django.db import models


class Patient(models.Model):
    identifier = models.CharField(primary_key=True, max_length=255)
