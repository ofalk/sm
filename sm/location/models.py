from django.db import models
from natural_keys import NaturalKeyModel
from django_countries.fields import CountryField

class Location(NaturalKeyModel):
  name = models.CharField(max_length = 45)
  country = CountryField()

  def __str__(self):
    if self.country:
      return "%s / %s" % (self.name, self.country)
    else:
      return "%s" % (self.name)

  class Meta:
    managed = True
    app_label = 'sm'
    unique_together = (('name','country'),)
