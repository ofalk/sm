from django.db import models
from django.db.models import Q
from django.urls import reverse
from simple_history.models import HistoricalRecords
from django.contrib.auth.models import Group
from taggit.managers import TaggableManager

from . import app_label


class ModelManager(models.Manager):
    def get_by_natural_key(self, name):
        return self.get(name=name)


class Model(models.Model):

    name = models.CharField(max_length=45)

    group = models.ForeignKey(
        Group,
        editable=False,
        blank=True,
        null=True,
        on_delete=models.PROTECT,
        related_name="patchtimes",
    )

    tags = TaggableManager(blank=True, related_name="patchtime_tags")

    objects = ModelManager()
    history = HistoricalRecords()

    def natural_key(self):
        return (self.name,)

    @classmethod
    def get_natural_key_fields(cls):
        return ["name"]

    @classmethod
    def get_natural_key_info(cls):
        return [("name", None)]

    def __str__(self):
        return "%s" % self.name

    def get_absolute_url(self):
        return reverse("%s:detail" % app_label, kwargs={"pk": self.pk})

    class Meta:
        db_table = "{}_{}".format("sm", app_label)
        constraints = [
            models.UniqueConstraint(
                fields=["name", "group"], name="unique_sm_patchtime_name_group"
            ),
            # PostgreSQL treats NULLs as distinct, so the constraint above
            # cannot deduplicate global (group=NULL) rows. Keep reference
            # data globally unique with a partial constraint.
            models.UniqueConstraint(
                fields=["name"],
                condition=Q(group__isnull=True),
                name="unique_sm_patchtime_global_name",
            ),
        ]
