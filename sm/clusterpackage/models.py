from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from simple_history.models import HistoricalRecords
from status.models import Model as StatusModel
from cluster.models import Model as ClusterModel
from clusterpackagetype.models import Model as ClusterpackagetypeModel
from django.contrib.auth.models import Group

from taggit.managers import TaggableManager

from . import app_label


class Protocol(models.TextChoices):
    HTTP = "http", _("HTTP")
    HTTPS = "https", _("HTTPS")
    TCP = "tcp", _("TCP")
    POSTGRES = "postgres", _("PostgreSQL")
    DNS = "dns", _("DNS")


class ClusterPackageManager(models.Manager):
    def get_by_natural_key(
        self, cluster, name, status=None, package_type=None, group=None
    ):
        if isinstance(cluster, (list, tuple)):
            cluster = cluster[0]
        if isinstance(status, (list, tuple)):
            status = status[0]
        if isinstance(package_type, (list, tuple)):
            package_type = package_type[0]
        if isinstance(group, (list, tuple)):
            group = group[0]
        return self.get(
            cluster__name=cluster,
            name=name,
            status__name=status,
            package_type__name=package_type,
            **(
                {"group__name": group} if group is not None else {"group__isnull": True}
            ),
        )


class Model(models.Model):
    objects = ClusterPackageManager()
    name = models.CharField(max_length=45)
    status = models.ForeignKey(
        StatusModel,
        related_name="%s_set" % app_label,
        on_delete=models.PROTECT,
    )
    cluster = models.ForeignKey(
        ClusterModel,
        related_name="%s_set" % app_label,
        on_delete=models.PROTECT,
    )
    description = models.CharField(max_length=256)
    monitoring = models.BooleanField(default=True, verbose_name="Monitoring")
    protocol = models.CharField(
        max_length=16,
        choices=Protocol.choices,
        default=Protocol.HTTP,
        verbose_name=_("Protocol"),
    )
    check_path = models.CharField(
        max_length=255,
        blank=True,
        default="",
        verbose_name=_("Check path"),
        help_text=_("HTTP path to probe, e.g. / or /-/readiness."),
    )
    expected_status = models.CharField(
        max_length=64,
        blank=True,
        default="",
        verbose_name=_("Expected status"),
        help_text=_("One or more status codes, e.g. 200,301,302,401."),
    )
    tls_sni = models.CharField(
        max_length=253,
        blank=True,
        default="",
        verbose_name=_("TLS SNI"),
        help_text=_("TLS server name if it differs from the host."),
    )
    check_module = models.CharField(
        max_length=64,
        blank=True,
        default="",
        verbose_name=_("Check module"),
        help_text=_("Blackbox module, e.g. http_2xx."),
    )
    metrics_host = models.CharField(
        max_length=253,
        blank=True,
        default="",
        verbose_name=_("Metrics host"),
        help_text=_("Metrics host if it differs from the check host."),
    )
    metrics_port = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_("Metrics port"),
    )
    runbook_url = models.URLField(
        max_length=2083,
        blank=True,
        null=True,
        verbose_name=_("Runbook URL"),
    )
    host = models.CharField(max_length=253, verbose_name="IP/Hostname")
    port = models.CharField(
        max_length=10, verbose_name="Port or ID", blank=True, null=True
    )
    package_type = models.ForeignKey(
        ClusterpackagetypeModel,
        related_name="%s_set" % app_label,
        on_delete=models.PROTECT,
    )
    tags = TaggableManager(blank=True, related_name="clusterpackage_tags")
    history = HistoricalRecords(related_name="clusterpackage_history")

    group = models.ForeignKey(
        Group,
        editable=False,
        blank=True,
        null=True,
        on_delete=models.PROTECT,
        related_name="clusterpackages",
    )

    def __str__(self):
        return "{}-{}".format(self.cluster, self.name)

    @property
    def sm_name(self) -> str:
        """Stable monitoring name: <cluster>/<package>."""
        return "{}/{}".format(self.cluster.name, self.name)

    def natural_key(self):
        return (
            self.cluster.natural_key()[0],
            self.name,
            self.status.natural_key()[0],
            self.package_type.natural_key()[0],
            self.group.name if self.group else None,
        )

    natural_key.dependencies = [
        "cluster.Model",
        "status.Model",
        "clusterpackagetype.Model",
        "auth.Group",
    ]

    @classmethod
    def get_natural_key_fields(cls):
        return [
            "cluster__name",
            "name",
            "status__name",
            "package_type__name",
            "group__name",
        ]

    @classmethod
    def get_natural_key_info(cls):
        return [
            ("cluster", ClusterModel),
            ("name", None),
            ("status", StatusModel),
            ("package_type", ClusterpackagetypeModel),
            ("group", Group),
        ]

    def get_absolute_url(self):

        return reverse("%s:detail" % app_label, kwargs={"pk": self.pk})

    class Meta:
        db_table = "{}_{}".format("sm", app_label)
        constraints = [
            models.UniqueConstraint(
                fields=["cluster", "name", "status", "package_type", "group"],
                name="unique_sm_clusterpackage_cluster_name_status_package_type_group",
            ),
        ]
