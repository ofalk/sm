from django.db import models
from natural_keys import NaturalKeyModel
from django.urls import reverse

from . import app_label


class Model(NaturalKeyModel):
    name = models.CharField(max_length=45, unique=True, verbose_name='Domain name')
    check_whois = models.BooleanField(default=True, verbose_name='Check whois via monitoring?')
    admin_email = models.CharField(max_length=45, unique=False, verbose_name='Whois admin email to check', blank=True, null=True)
    tech_email = models.CharField(max_length=45, unique=False, verbose_name='Whois tech email to check', blank=True, null=True)

    def __str__(self):
        return "%s" % self.name

    def get_absolute_url(self):
        return reverse('%s:detail' % app_label, kwargs={'pk': self.pk})

    class Meta:
        managed = True
        app_label = app_label
        db_table = '%s_%s' % ('sm', app_label)
