from django.db import models
from patchtime.models import Patchtime
from status.models import Status
from domain.models import Domain
from location.models import Location
from django.urls import reverse
from django.utils.timezone import now


class Server(models.Model):
    hostname = models.CharField(max_length=45)
    domain = models.ForeignKey(Domain, on_delete=models.PROTECT, default=1)
    delivery_date = models.DateField(default=now)
    install_date = models.DateField(default=now)
    last_update = models.DateTimeField(auto_now=True)
    documentation_url = models.URLField(max_length=2083, blank=True, null=True)
    memory_in_mb = models.IntegerField(blank=True, null=True)
    location = models.ForeignKey(Location, on_delete=models.PROTECT)

    status = models.ForeignKey(Status, on_delete=models.PROTECT, default=1)

    # => application model
    # application = models.CharField(max_length=100, blank=True, null=True)

    # => rack model
    # rack = models.CharField(max_length=45, blank=True, null=True)

    # network!
    primary_ip = models.GenericIPAddressField(blank=True, null=True)
    management_ip = models.GenericIPAddressField(blank=True, null=True)
    management_hostname = models.CharField(max_length=45,
                                           blank=True, null=True)
    delivery_note_id = models.CharField(max_length=45, blank=True, null=True)
    serial_nr = models.CharField(max_length=60, blank=True, null=True)
    description = models.CharField(max_length=100, blank=True, null=True)

    patchtime = models.ForeignKey(Patchtime, null=True, default=None)

    # patch time
    # tags

    def __str__(self):
        return "%s" % self.hostname

    def get_absolute_url(self):
        return reverse('server:detail', kwargs={'pk': self.pk})

    class Meta:
        managed = True
        unique_together = (('hostname', 'status'),)
        app_label = 'sm'
