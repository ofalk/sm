from django.db import models
from django.urls import reverse
from simple_history.models import HistoricalRecords
from vendor.models import Model as VendorModel

from . import app_label


class ClusterSoftwareManager(models.Manager):
    def get_by_natural_key(self, vendor, name, version):
        if isinstance(vendor, (list, tuple)):
            vendor = vendor[0]
        return self.get(vendor__name=vendor, name=name, version=version)


class Model(models.Model):
    objects = ClusterSoftwareManager()
    history = HistoricalRecords()
    name = models.CharField(max_length=45)
    version = models.CharField(max_length=45, default="", blank=True)
    vendor = models.ForeignKey(
        VendorModel,
        related_name="%s_set" % app_label,
        related_query_name="%s" % app_label,
        on_delete=models.PROTECT,
    )

    def __str__(self):
        if self.name and self.version:
            return "{} {}".format(self.name, self.version)
        if self.name and not self.version:
            return "%s" % (self.name)
        return self  # pragma: no cover

    def natural_key(self):
        return self.vendor.natural_key() + (self.name, self.version)

    natural_key.dependencies = ["vendor.Model"]

    @classmethod
    def get_natural_key_fields(cls):
        return ["vendor__name", "name", "version"]

    @classmethod
    def get_natural_key_info(cls):
        return [("vendor", VendorModel), ("name", None), ("version", None)]

    def get_absolute_url(self):

        return reverse("%s:detail" % app_label, kwargs={"pk": self.pk})

    class Meta:
        db_table = "{}_{}".format("sm", app_label)
        constraints = [
            models.UniqueConstraint(
                fields=["vendor", "name", "version"],
                name="unique_sm_clustersoftware_vendor_name_version",
            )
        ]
