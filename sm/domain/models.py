from django.db import models
from natural_keys import NaturalKeyModel
from django.urls import reverse


class Domain(NaturalKeyModel):
    name = models.CharField(max_length=45, unique=True)

    def __str__(self):
        return "%s" % self.name

    def get_absolute_url(self):
        return reverse('domain:detail', kwargs={'pk': self.pk})

    class Meta:
        managed = True
        app_label = 'sm'
