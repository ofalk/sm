from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from simple_history.models import HistoricalRecords
from django.contrib.auth.models import Group
from taggit.managers import TaggableManager

from . import app_label


class ModelManager(models.Manager):
    def get_by_natural_key(self, name):
        return self.get(name=name)


class Model(models.Model):

    name = models.CharField(max_length=45, verbose_name="Domain name")
    monitoring = models.BooleanField(default=False, verbose_name="Monitoring")
    check_http = models.BooleanField(default=True, verbose_name=_("HTTP check"))
    check_tls = models.BooleanField(default=True, verbose_name=_("TLS check"))
    expected_status = models.CharField(
        max_length=64,
        blank=True,
        default="",
        verbose_name=_("Expected status"),
        help_text=_("One or more status codes, e.g. 200,301,302."),
    )
    tls_sni = models.CharField(
        max_length=253,
        blank=True,
        default="",
        verbose_name=_("TLS SNI"),
        help_text=_("TLS server name if it differs from the domain."),
    )

    group = models.ForeignKey(
        Group,
        editable=False,
        blank=True,
        null=True,
        on_delete=models.PROTECT,
        related_name="domains",
    )

    tags = TaggableManager(blank=True, related_name="domain_tags")

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

    @property
    def sm_name(self) -> str:
        """Stable monitoring name: the domain name itself."""
        return self.name

    def get_absolute_url(self):
        return reverse("%s:detail" % app_label, kwargs={"pk": self.pk})

    class Meta:
        db_table = "{}_{}".format("sm", app_label)
        constraints = [
            models.UniqueConstraint(
                fields=["name", "group"], name="unique_sm_domain_name_group"
            ),
            # PostgreSQL treats NULLs as distinct, so the constraint above
            # cannot deduplicate global (group=NULL) rows. Keep reference
            # data globally unique with a partial constraint.
            models.UniqueConstraint(
                fields=["name"],
                condition=Q(group__isnull=True),
                name="unique_sm_domain_global_name",
            ),
        ]
