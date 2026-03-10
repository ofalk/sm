from django.db import models
from patchtime.models import Model as PatchtimeModel
from status.models import Model as StatusModel
from domain.models import Model as DomainModel
from location.models import Model as LocationModel
from operatingsystem.models import Model as OperatingsystemModel
from servermodel.models import Model as ServermodelModel
from cluster.models import Model as ClusterModel
from django.urls import reverse
from django.utils.timezone import now
from simple_history.models import HistoricalRecords

from . import app_label


class ServerManager(models.Manager):
    def get_by_natural_key(self, hostname, status):
        if isinstance(status, (list, tuple)):
            status = status[0]
        return self.get(hostname=hostname, status__name=status)


class Model(models.Model):
    objects = ServerManager()
    hostname = models.CharField(max_length=45)
    domain = models.ForeignKey(DomainModel, on_delete=models.PROTECT, default=1)
    delivery_date = models.DateField(default=now)
    install_date = models.DateField(default=now)
    last_update = models.DateTimeField(auto_now=True)
    documentation_url = models.URLField(max_length=2083, blank=True, null=True)
    memory_in_mb = models.IntegerField(blank=True, null=True)
    monitoring_from_puppet = models.BooleanField(default=False)
    location = models.ForeignKey(
        LocationModel,
        on_delete=models.PROTECT,
        null=True,
        related_name="%s_set" % app_label,
        related_query_name="%s" % app_label,
    )
    operatingsystem = models.ForeignKey(
        OperatingsystemModel,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="%s_set" % app_label,
        related_query_name="%s" % app_label,
    )

    status = models.ForeignKey(
        StatusModel,
        on_delete=models.PROTECT,
        default=1,
        related_name="%s_set" % app_label,
        related_query_name="%s" % app_label,
    )

    servermodel = models.ForeignKey(
        ServermodelModel,
        on_delete=models.PROTECT,
        null=True,
        related_name="%s_set" % app_label,
        related_query_name="%s" % app_label,
    )

    cluster = models.ForeignKey(
        ClusterModel,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="%s_set" % app_label,
        related_query_name="%s" % app_label,
    )

    # => application model
    # application = models.CharField(max_length=100, blank=True, null=True)

    # => rack model
    # rack = models.CharField(max_length=45, blank=True, null=True)

    # network!
    primary_ip = models.GenericIPAddressField(blank=True, null=True)
    management_ip = models.GenericIPAddressField(blank=True, null=True)
    management_hostname = models.CharField(max_length=45, blank=True, null=True)
    delivery_note_id = models.CharField(max_length=45, blank=True, null=True)
    serial_nr = models.CharField(max_length=60, blank=True, null=True)
    description = models.CharField(max_length=100, blank=True, null=True)

    patchtime = models.ForeignKey(
        PatchtimeModel,
        null=True,
        default=None,
        on_delete=models.PROTECT,
        related_name="%s_set" % app_label,
        related_query_name="%s" % app_label,
    )

    history = HistoricalRecords()

    def __str__(self):
        return "%s" % self.hostname

    def natural_key(self):
        return (self.hostname,) + self.status.natural_key()

    natural_key.dependencies = ["status.Model"]

    @classmethod
    def get_natural_key_fields(cls):
        return ["hostname", "status__name"]

    @classmethod
    def get_natural_key_info(cls):
        return [("hostname", None), ("status", StatusModel)]

    def get_absolute_url(self):
        return reverse("server:detail", kwargs={"pk": self.pk})

    class Meta:
        db_table = "{}_{}".format("sm", app_label)
        constraints = [
            models.UniqueConstraint(
                fields=["hostname", "status"], name="unique_sm_server_hostname_status"
            )
        ]
