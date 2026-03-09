from django.db import models
from django.urls import reverse
from vendor.models import Model as VendorModel

from . import app_label


class ServerModelManager(models.Manager):
    def get_by_natural_key(self, vendor, name):
        if isinstance(vendor, (list, tuple)):
            vendor = vendor[0]
        return self.get(vendor__name=vendor, name=name)


class Model(models.Model):
    objects = ServerModelManager()
    name = models.CharField(max_length=45)
    vendor = models.ForeignKey(
        VendorModel,
        null=False,
        default=None,
        related_name="%s_set" % app_label,
        related_query_name="%s" % app_label,
        on_delete=models.PROTECT,
    )

    def __str__(self):
        return "{} {}".format(self.vendor.name, self.name)

    def natural_key(self):
        return self.vendor.natural_key() + (self.name,)

    natural_key.dependencies = ["vendor.Model"]

    @classmethod
    def get_natural_key_fields(cls):
        return ["vendor__name", "name"]

    @classmethod
    def get_natural_key_info(cls):
        return [("vendor", VendorModel), ("name", None)]

    def get_absolute_url(self):

        return reverse("%s:detail" % app_label, kwargs={"pk": self.pk})

    class Meta:
        db_table = "{}_{}".format("sm", app_label)
        constraints = [
            models.UniqueConstraint(
                fields=["vendor", "name"], name="unique_sm_servermodel_vendor_name"
            )
        ]
