from django.db import models
from natural_keys import NaturalKeyModel
from django.urls import reverse
from vendor.models import Vendor

from django.core.exceptions import ObjectDoesNotExist

from . import app_label


class OperatingsystemManager(models.Manager):
    """
    Special manager to ease the access to Operating system objects
    eg. RHEL6.1, RHEL 6.1, SLES10, SLES 10.1 should all work well
    """
    def get_by_natural_key(self, vendor=None, version=None):
        """
        Ease access to OS objects, by providing a lot of different options
        to query for 'em. See also OperatingSystemManager.__doc__
        :model:`sm.models.OperatingsystemManager`
        """
        if vendor is None and version is None:
            raise ObjectDoesNotExist("Nothing to query")

        vendorobj = None
        try:
            vendorobj = Vendor.objects.get(name=vendor)
        except Exception as e:
            pass
        object = None
        try:
            object = self.get(vendor=vendorobj, version=version)
            return object
        except Exception as e:
            pass

        if version is None and vendor is not None:
            version = vendor
            vendor = None

        if object is None and \
           version.__class__ != tuple and \
           version.__class__ != list and \
           version.__class__ != dict:
            if version[0:7] == 'Red Hat':
                vendorobj = Vendor.objects.get(name='Red Hat')
                vers = version[7:].lstrip()
                if len(vers) == 1:
                    vers += '.0'
                object = self.get(vendor=vendorobj, version=vers)
            elif version[0:4] == 'RHEL':
                vendorobj = Vendor.objects.get(name='Red Hat')
                vers = version[4:].lstrip()
                if len(vers) == 1:
                    vers += '.0'
                object = self.get(vendor=vendorobj, version=vers)
            elif version[0:4] == 'SUSE' or version[0:4] == 'SLES':
                vendorobj = Vendor.objects.get(name='Novell')
                object = self.get(
                    vendor=vendorobj,
                    version=version[4:].lstrip())
        elif version.__class__ == tuple or version.__class__ == list:
            try:
                vendorobj = Vendor.objects.get(name=version[0])
                object = self.get(vendor=vendorobj, version=version[1])
                return object
            except Exception as e:  # pragma: no cover
                print("Exception: %s" % e)  # pragma: no cover
                pass  # pragma: no cover
        else:
            raise Exception('No idea how to handle query with %s' %
                            version.__class__)

        if object is None:
            vendorobj = Vendor.objects.get(name=vendor)
            self.get(vendor=vendorobj, version=version)

        return object


class Operatingsystem(NaturalKeyModel):
    objects = OperatingsystemManager()
    version = models.CharField(max_length=45)
    vendor = models.ForeignKey(Vendor, null=False, default=None)

    def __str__(self):
        return "%s %s" % (self.vendor.name, self.version)

    def get_absolute_url(self):
        return reverse('operatingsystem:detail', kwargs={'pk': self.pk})

    def natural_key(self):
        return (self.vendor.name, self.version)

    class Meta:
        managed = True
        app_label = app_label
        db_table = '%s_%s' % ('sm', app_label)
        unique_together = (('vendor', 'version'),)
