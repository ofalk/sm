from django.db import models
from natural_keys import NaturalKeyModel
from django.urls import reverse
from vendor.models import Vendor


class Servermodel(NaturalKeyModel):
    name = models.CharField(max_length=45)
    vendor = models.ForeignKey(Vendor, null=False, default=None)

    def __str__(self):
        return "%s %s" % (self.vendor.name, self.name)

    def get_absolute_url(self):
        return reverse('servermodel:detail', kwargs={'pk': self.pk})

    def natural_key(self):
        return (self.vendor.name, self.name)

    class Meta:
        managed = True
        app_label = 'sm'
        unique_together = (('vendor', 'name'),)
