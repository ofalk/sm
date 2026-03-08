"""
All models for our cluster module
Current only one model is defined:
    1. ***Model*** - Main model for cluster - best imported as
       from cluster.models import Model as ClusterModel
"""
from django.db import models
from natural_keys import NaturalKeyModel
from django.urls import reverse
from clustersoftware.models import Model as ClustersoftwareModel
from django.contrib.auth.models import Group

from . import app_label

# === Model for cluster ===


class Model(NaturalKeyModel):

    """
    The Model class in 'cluster', defined the cluster model.
    Clusters have several servers (reverse related via Model in 'server'
    Each cluster has the following fields:
        name - how the cluster is named
        clustersoftware - relation to clustersoftware model
        group - the (user) group this cluster belongs to
    """
    name = models.CharField(max_length=45, unique=True)
    clustersoftware = models.ForeignKey(ClustersoftwareModel,
                                        related_name='%s_set' % app_label,
                                        related_query_name='%s' % app_label,
                                        blank=True, null=True,
                                        on_delete=models.PROTECT)

    group = models.ForeignKey(Group, editable=False,
                              blank=True,
                              null=True,
                              on_delete=models.PROTECT)

    # === __str__ ===
    def __str__(self):
        return '%s' % (self.name)

    # === get_absolute_url ===
    def get_absolute_url(self):
        return reverse('%s:detail' % app_label, kwargs={'pk': self.pk})

    # === natural_key ===


    # === Class meta data ===
    class Meta:
        managed = True
        app_label = app_label
        db_table = '%s_%s' % ('sm', app_label)
