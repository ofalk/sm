from django.utils.translation import gettext_lazy as _

from .models import Model
from sm.forms import SMForm, SMFormDisabled, UniquePerGroupMixin


class Form(UniquePerGroupMixin, SMForm):
    field_groups = [
        {
            "title": _("Domain"),
            "fields": ["name", "monitoring"],
        },
        {
            "title": _("Checks"),
            "fields": [
                "check_http",
                "check_tls",
                "expected_status",
                "tls_sni",
            ],
        },
        {
            "title": _("Tags"),
            "fields": ["tags"],
            "wide": ["tags"],
        },
    ]

    class Meta(SMForm.Meta):
        model = Model


class FormDisabled(Form, SMFormDisabled):
    pass
