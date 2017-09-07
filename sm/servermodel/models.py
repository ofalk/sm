from django.db import models
from natural_keys import NaturalKeyModel
from django.urls import reverse
from vendor.models import Model as VendorModel

from . import app_label


class Model(NaturalKeyModel):
    name = models.CharField(max_length=45)
    vendor = models.ForeignKey(VendorModel, null=False, default=None,
                               related_name='%s_set' % app_label,
                               related_query_name='%s' % app_label)

    def __str__(self):
        return "%s %s" % (self.vendor.name, self.name)

    def get_absolute_url(self):
        return reverse('%s:detail' % app_label, kwargs={'pk': self.pk})

    def natural_key(self):
        return (self.vendor.name, self.name)

    class Meta:
        managed = True
        app_label = app_label
        db_table = '%s_%s' % ('sm', app_label)
        unique_together = (('vendor', 'name'),)
