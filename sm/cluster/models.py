from django.db import models
from natural_keys import NaturalKeyModel
from django.urls import reverse
from clustersoftware.models import Model as ClustersoftwareModel
from django.contrib.auth.models import Group

from . import app_label


class Model(NaturalKeyModel):
    name = models.CharField(max_length=45, unique=True)
    clustersoftware = models.ForeignKey(ClustersoftwareModel,
                                        related_name='%s_set' % app_label,
                                        related_query_name='%s' % app_label,
                                        blank=True, null=True)
    group = models.ForeignKey(Group, editable=False,
                              blank=False,
                              null=False)

    def __str__(self):
        return '%s' % (self.name)

    def get_absolute_url(self):
        return reverse('%s:detail' % app_label, kwargs={'pk': self.pk})

    def natural_key(self):
        return (self.name,)

    class Meta:
        managed = True
        app_label = app_label
        db_table = '%s_%s' % ('sm', app_label)
