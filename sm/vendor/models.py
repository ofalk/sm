from django.db import models
from natural_keys import NaturalKeyModel

class Vendor(NaturalKeyModel):
  name = models.CharField(max_length = 45, unique = True)

  def __str__(self):
    return "%s" % self.name

  class Meta:
    managed = True
    app_label = 'sm'
