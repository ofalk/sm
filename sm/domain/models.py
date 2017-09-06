from django.db import models
from natural_keys import NaturalKeyModel
from django.urls import reverse

from . import app_name

app_name = app_name


class Model(NaturalKeyModel):
    name = models.CharField(max_length=45, unique=True)

    def __str__(self):
        return "%s" % self.name

    def get_absolute_url(self):
        return reverse('%s:detail' % app_name, kwargs={'pk': self.pk})

    class Meta:
        managed = True
        app_label = 'sm'
        db_table = '%s_%s' % (app_label, app_name)
