from django.db import models
from django_countries.fields import CountryField
from django.urls import reverse
from simple_history.models import HistoricalRecords
from django.contrib.auth.models import Group
from taggit.managers import TaggableManager

from . import app_label


class LocationManager(models.Manager):
    def get_by_natural_key(self, name, country):
        return self.get(name=name, country=country)


class Model(models.Model):
    objects = LocationManager()
    history = HistoricalRecords()
    name = models.CharField(max_length=45)
    country = CountryField()

    group = models.ForeignKey(
        Group,
        editable=False,
        blank=True,
        null=True,
        on_delete=models.PROTECT,
        related_name="locations",
    )

    tags = TaggableManager(blank=True, related_name="location_tags")

    def __str__(self):
        if self.country:
            return "{} / {}".format(self.name, self.country)
        else:
            return "%s" % (self.name)

    def natural_key(self):
        return (self.name, str(self.country))

    @classmethod
    def get_natural_key_fields(cls):
        return ["name", "country"]

    @classmethod
    def get_natural_key_info(cls):
        return [("name", None), ("country", None)]

    def get_absolute_url(self):

        return reverse("%s:detail" % app_label, kwargs={"pk": self.pk})

    class Meta:
        db_table = "{}_{}".format("sm", app_label)
        constraints = [
            models.UniqueConstraint(
                fields=["name", "country", "group"],
                name="unique_sm_location_name_country_group",
            )
        ]
