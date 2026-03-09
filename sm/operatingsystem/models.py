from django.db import models
from django.urls import reverse
from vendor.models import Model as VendorModel

from django.core.exceptions import ObjectDoesNotExist

from . import app_label


class Manager(models.Manager):
    """
    Special manager to ease the access to Operatingsystem objects
    eg. RHEL6.1, RHEL 6.1, SLES10, SLES 10.1 should all work well
    """

    def get_by_natural_key(self, vendor=None, version=None):
        """
        Ease access to OS objects, by providing a lot of different options
        to query for 'em. See also operatingsystem.models.Manager.__doc__
        :model:`sm.operatingsystem.models.Manager`
        """
        if vendor is None and version is None:
            raise ObjectDoesNotExist("Nothing to query")

        # Handle natural key tuple if passed as single arg (Django's default)
        if version is None and isinstance(vendor, (list, tuple)):
            version = vendor[1]
            vendor = vendor[0]

        vendorobj = None
        try:
            if isinstance(vendor, str):
                vendorobj = VendorModel.objects.get(name=vendor)
            else:
                vendorobj = vendor
        except Exception:
            pass
        object = None
        try:
            object = self.get(vendor=vendorobj, version=version)
            return object
        except Exception:
            pass

        if version is None and vendor is not None:
            version = vendor
            vendor = None

        if object is None and not isinstance(version, (tuple, list, dict)):
            if version[0:7] == "Red Hat":
                vendorobj = VendorModel.objects.get(name="Red Hat")
                vers = version[7:].lstrip()
                if len(vers) == 1:
                    vers += ".0"
                object = self.get(vendor=vendorobj, version=vers)
            elif version[0:4] == "RHEL":
                vendorobj = VendorModel.objects.get(name="Red Hat")
                vers = version[4:].lstrip()
                if len(vers) == 1:
                    vers += ".0"
                object = self.get(vendor=vendorobj, version=vers)
            elif version[0:4] == "SUSE" or version[0:4] == "SLES":
                vendorobj = VendorModel.objects.get(name="Novell")
                object = self.get(vendor=vendorobj, version=version[4:].lstrip())
        elif isinstance(version, (tuple, list)):
            try:
                vendorobj = VendorModel.objects.get(name=version[0])
                object = self.get(vendor=vendorobj, version=version[1])
                return object
            except Exception as e:  # pragma: no cover
                print("Exception: %s" % e)  # pragma: no cover
                pass  # pragma: no cover
        else:
            raise Exception("No idea how to handle query with %s" % version.__class__)

        if object is None:
            vendorobj = VendorModel.objects.get(name=vendor)
            self.get(vendor=vendorobj, version=version)

        return object


class Model(models.Model):
    objects = Manager()
    version = models.CharField(max_length=45)
    vendor = models.ForeignKey(
        VendorModel,
        null=False,
        default=None,
        related_name="%s_set" % app_label,
        related_query_name="%s" % app_label,
        on_delete=models.PROTECT,
    )

    def __str__(self):
        return "{} {}".format(self.vendor.name, self.version)

    def natural_key(self):
        return self.vendor.natural_key() + (self.version,)

    natural_key.dependencies = ["vendor.Model"]

    @classmethod
    def get_natural_key_fields(cls):
        return ["vendor__name", "version"]

    @classmethod
    def get_natural_key_info(cls):
        return [("vendor", VendorModel), ("version", None)]

    def get_absolute_url(self):
        return reverse("%s:detail" % app_label, kwargs={"pk": self.pk})

    class Meta:
        db_table = "{}_{}".format("sm", app_label)
        constraints = [
            models.UniqueConstraint(
                fields=["vendor", "version"],
                name="unique_sm_operatingsystem_vendor_version",
            )
        ]
