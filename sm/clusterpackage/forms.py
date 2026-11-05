from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy

from .models import Model, Protocol
from sm.forms import SMForm, SMFormDisabled


class Form(SMForm):
    field_groups = [
        {
            "title": gettext_lazy("Package"),
            "fields": [
                "name",
                "status",
                "cluster",
                "package_type",
                "monitoring",
            ],
        },
        {
            "title": gettext_lazy("Endpoint"),
            "fields": [
                "host",
                "port",
                "protocol",
                "metrics_host",
                "metrics_port",
            ],
        },
        {
            "title": gettext_lazy("HTTP / TLS check"),
            "fields": [
                "check_path",
                "expected_status",
                "tls_sni",
                "check_module",
            ],
        },
        {
            "title": gettext_lazy("Details"),
            "fields": ["description", "runbook_url", "tags"],
            "wide": ["description", "runbook_url", "tags"],
        },
    ]

    class Meta(SMForm.Meta):
        model = Model

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        kwargs["user"] = user  # let SMForm scope FK choices to the user
        super().__init__(*args, **kwargs)
        # New endpoint metadata has model defaults; keep it optional for older
        # clients/forms that do not submit it.
        self.fields["protocol"].required = False

    def clean_protocol(self):
        return self.cleaned_data.get("protocol") or Protocol.HTTP

    def clean(self):
        cleaned_data = super().clean()
        cluster = cleaned_data.get("cluster")
        name = cleaned_data.get("name")
        status = cleaned_data.get("status")
        package_type = cleaned_data.get("package_type")
        if None in (cluster, name, status, package_type):
            return cleaned_data
        # Packages inherit their cluster's tenant group. On update the group is
        # immutable (editable=False) so the existing instance group governs.
        if self.instance and self.instance.pk:
            group = self.instance.group
        else:
            group = cluster.group
        queryset = Model.objects.filter(
            cluster=cluster,
            name=name,
            status=status,
            package_type=package_type,
        )
        if group is not None:
            queryset = queryset.filter(group=group)
        else:
            queryset = queryset.filter(group__isnull=True)
        if self.instance and self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            self.add_error(
                None,
                _(
                    "A cluster package with this cluster, name, status and "
                    "package type already exists."
                ),
            )
        return cleaned_data


class FormDisabled(Form, SMFormDisabled):
    """Read-only variant; monitoring has a dedicated toggle in the header."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields.pop("monitoring", None)
        self.layout = self.build_layout()
