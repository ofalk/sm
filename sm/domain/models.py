from django.db import models
from django.urls import reverse
from simple_history.models import HistoricalRecords

from . import app_label


class ModelManager(models.Manager):
    def get_by_natural_key(self, name):
        return self.get(name=name)


class Model(models.Model):

    name = models.CharField(max_length=45, unique=True, verbose_name="Domain name")

    objects = ModelManager()
    history = HistoricalRecords()

    def natural_key(self):
        return (self.name,)

    @classmethod
    def get_natural_key_fields(cls):
        return ["name"]

    @classmethod
    def get_natural_key_info(cls):
        return [("name", None)]

    def __str__(self):
        return "%s" % self.name

    def get_absolute_url(self):
        return reverse("%s:detail" % app_label, kwargs={"pk": self.pk})

    class Meta:
        db_table = "{}_{}".format("sm", app_label)
