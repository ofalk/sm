from django.db import models
from natural_keys import NaturalKeyModel
from django.urls import reverse
from status.models import Model as StatusModel
from cluster.models import Model as ClusterModel
from clusterpackagetype.models import Model as ClusterpackagetypeModel

from taggit.managers import TaggableManager

from . import app_label


class Model(NaturalKeyModel):
    name = models.CharField(max_length=45)
    status = models.ForeignKey(StatusModel,
                               related_name='%s_set' % app_label,
                               related_query_name='%s_set' % app_label,
                               on_delete=models.PROTECT)
    cluster = models.ForeignKey(ClusterModel,
                                related_name='%s_set' % app_label,
                                related_query_name='%s_set' % app_label,
                                on_delete=models.PROTECT)
    description = models.CharField(max_length=256)
    host = models.CharField(max_length=253, verbose_name='IP/Hostname')
    port = models.CharField(max_length=10,
                            verbose_name='Port or ID',
                            blank=True,
                            null=True)
    package_type = models.ForeignKey(ClusterpackagetypeModel,
                                     related_name='%s_set' % app_label,
                                     related_query_name='%s_set' % app_label,
                                     on_delete=models.PROTECT)
    tags = TaggableManager(blank=True)

    def __str__(self):
        return "%s-%s" % (self.cluster, self.name)

    def get_absolute_url(self):
        return reverse('%s:detail' % app_label, kwargs={'pk': self.pk})

    def natural_key(self):
        return (self.cluster, self.name)

    class Meta:
        managed = True
        app_label = app_label
        db_table = '%s_%s' % ('sm', app_label)
        unique_together = (('cluster', 'name',),)
