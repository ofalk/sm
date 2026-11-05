from .models import (
    Criticality,
    Model as ServerModel,
    MonitoringProfile,
)
from sm.forms import SMForm, SMFormDisabled
from status.models import Model as StatusModel

from django.forms import DateInput
from django import forms
from django.utils.translation import gettext_lazy as _


class Form(SMForm):
    """
    Override default form behaviour; Make sure 'In Use' is the default/initial
    value
    """

    field_groups = [
        {
            "title": _("Identity"),
            "fields": [
                "hostname",
                "domain",
                "status",
                "location",
                "cluster",
                "servermodel",
            ],
        },
        {
            "title": _("Hardware & Operating System"),
            "fields": [
                "operatingsystem",
                "memory_in_mb",
                "serial_nr",
                "delivery_note_id",
            ],
        },
        {
            "title": _("Network"),
            "fields": [
                "primary_ip",
                "management_ip",
                "management_hostname",
                "rack",
            ],
        },
        {
            "title": _("Lifecycle & Monitoring"),
            "fields": [
                "delivery_date",
                "install_date",
                "decommission_date",
                "monitoring_from_puppet",
                "monitoring_profile",
                "criticality",
                "maintenance_window",
            ],
        },
        {
            "title": _("Ownership & Runbooks"),
            "fields": ["owner_team", "runbook_url"],
        },
        {
            "title": _("Prometheus Metadata"),
            "fields": ["monitoring_labels", "exporter_endpoints"],
            "wide": ["monitoring_labels", "exporter_endpoints"],
        },
        {
            "title": _("Operations"),
            "fields": [
                "application",
                "patchtime",
                "documentation_url",
                "description",
                "tags",
            ],
            "wide": ["documentation_url", "description", "tags"],
        },
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # New monitoring metadata has model defaults. Keep the fields optional
        # for older clients/forms that do not submit them.
        self.fields["monitoring_profile"].required = False
        self.fields["criticality"].required = False
        try:
            default_status = StatusModel.objects.filter(name="In use").first()
            if default_status:
                self.fields["status"].initial = default_status.id
        except Exception as e:  # noqa # flake8: noqa # NOQA # pragma: no cover
            print('No status "In Use" found: %s' % e)

    def clean_monitoring_profile(self):
        return self.cleaned_data.get("monitoring_profile") or MonitoringProfile.NONE

    def clean_criticality(self):
        return self.cleaned_data.get("criticality") or Criticality.NORMAL

    class Meta(SMForm.Meta):
        model = ServerModel
        widgets = {
            "delivery_date": DateInput(attrs={"class": "date-input"}),
            "install_date": DateInput(attrs={"class": "date-input"}),
        }


class FormDisabled(Form, SMFormDisabled):
    """
    Read-only variant for the detail page. Monitoring gets its own toggle
    control in the card header, so it is removed from the disabled form.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields.pop("monitoring_from_puppet", None)
        self.layout = self.build_layout()


class BulkActionForm(forms.Form):
    status = forms.ModelChoiceField(
        queryset=StatusModel.objects.all(),
        required=False,
        label="Change Status to",
        empty_label="--- No Change ---",
    )
    delete = forms.BooleanField(required=False, label="Delete Selected Servers")
    decommission = forms.BooleanField(
        required=False, label="Decommission (set decommission date)"
    )
