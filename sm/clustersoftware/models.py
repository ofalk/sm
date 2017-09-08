from django.db import models
from natural_keys import NaturalKeyModel
from django.urls import reverse
from vendor.models import Model as VendorModel

from . import app_label


class Model(NaturalKeyModel):
    name = models.CharField(max_length=45)
    version = models.CharField(max_length=45, default='', blank=True)
    vendor = models.ForeignKey(VendorModel,
                               related_name='%s_set' % app_label,
                               related_query_name='%s' % app_label)

    def __str__(self):
        if self.name and self.version:
            return '%s %s' % (self.name, self.version)
        if self.name and not self.version:
            return '%s' % (self.name)
        return self

    def get_absolute_url(self):
        return reverse('%s:detail' % app_label, kwargs={'pk': self.pk})

    def natural_key(self):
        return (self.vendor.name, self.name, self.version)

    class Meta:
        managed = True
        app_label = app_label
        db_table = '%s_%s' % ('sm', app_label)
        unique_together = (('vendor', 'name', 'version'),)
