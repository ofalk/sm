from django.db import models
from django.urls import reverse
from simple_history.models import HistoricalRecords
from status.models import Model as StatusModel
from cluster.models import Model as ClusterModel
from clusterpackagetype.models import Model as ClusterpackagetypeModel

from taggit.managers import TaggableManager
import uuid

from . import app_label


class ClusterPackageManager(models.Manager):

    def get_by_natural_key(self, cluster, name):
        if isinstance(cluster, (list, tuple)):
            cluster = cluster[0]
        return self.get(cluster__name=cluster, name=name)


class Model(models.Model):
    objects = ClusterPackageManager()
    name = models.CharField(max_length=45)
    status = models.ForeignKey(
        StatusModel,
        related_name="%s_set" % app_label,
        on_delete=models.PROTECT,
    )
    cluster = models.ForeignKey(
        ClusterModel,
        related_name="%s_set" % app_label,
        on_delete=models.PROTECT,
    )
    description = models.CharField(max_length=256)
    host = models.CharField(max_length=253, verbose_name="IP/Hostname")
    port = models.CharField(
        max_length=10, verbose_name="Port or ID", blank=True, null=True
    )
    package_type = models.ForeignKey(
        ClusterpackagetypeModel,
        related_name="%s_set" % app_label,
        on_delete=models.PROTECT,
    )
    tags = TaggableManager(blank=True)
    history = HistoricalRecords(related_name="clusterpackage_history")

    def __str__(self):
        return "{}-{}".format(self.cluster, self.name)

    def natural_key(self):
        return self.cluster.natural_key() + (self.name,)

    natural_key.dependencies = ["cluster.Model"]

    @classmethod
    def get_natural_key_fields(cls):
        return ["cluster__name", "name"]

    @classmethod
    def get_natural_key_info(cls):
        return [("cluster", ClusterModel), ("name", None)]

    def get_absolute_url(self):

        return reverse("%s:detail" % app_label, kwargs={"pk": self.pk})

    class Meta:
        db_table = "{}_{}".format("sm", app_label)
        constraints = [
            models.UniqueConstraint(
                fields=["cluster", "name"], name="unique_sm_clusterpackage_cluster_name"
            )
        ]
