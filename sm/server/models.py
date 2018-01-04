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

from . import app_label


class Model(models.Model):
    hostname = models.CharField(max_length=45)
    domain = models.ForeignKey(DomainModel, on_delete=models.PROTECT,
                               default=1)
    delivery_date = models.DateField(default=now)
    install_date = models.DateField(default=now)
    last_update = models.DateTimeField(auto_now=True)
    documentation_url = models.URLField(max_length=2083, blank=True, null=True)
    memory_in_mb = models.IntegerField(blank=True, null=True)
    monitoring_from_puppet = models.BooleanField(default=False)
    location = models.ForeignKey(LocationModel,
                                 on_delete=models.PROTECT,
                                 null=True)
    operatingsystem = models.ForeignKey(OperatingsystemModel,
                                        on_delete=models.PROTECT,
                                        null=True, blank=True,
                                        related_name='%s_set' % app_label,
                                        related_query_name='%s' % app_label)

    status = models.ForeignKey(StatusModel, on_delete=models.PROTECT,
                               default=1)

    servermodel = models.ForeignKey(ServermodelModel, on_delete=models.PROTECT,
                                    null=True)

    cluster = models.ForeignKey(ClusterModel, on_delete=models.PROTECT,
                                null=True, blank=True,
                                related_name='%s_set' % app_label,
                                related_query_name='%s' % app_label)

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

    patchtime = models.ForeignKey(PatchtimeModel,
                                  null=True, default=None,
                                  on_delete=models.PROTECT)

    def __str__(self):
        return "%s" % self.hostname

    def get_absolute_url(self):
        return reverse('server:detail', kwargs={'pk': self.pk})

    class Meta:
        managed = True
        unique_together = (('hostname', 'status'),)
        app_label = app_label
        db_table = '%s_%s' % ('sm', app_label)
