from .models import Model
from sm.forms import SMForm, SMFormDisabled
from sm.mixins import filter_queryset_for_user
from server.models import Model as ServerModel

from django.forms import ModelMultipleChoiceField
from django.utils.translation import gettext_lazy as _


class Form(SMForm):
    """
    Form providing an extra field; All ServerModels ordered by cluster and
    hostname, additionally sets the initial list in __init__()
    """

    field_groups = [
        {
            "title": _("Cluster"),
            "fields": ["name", "clustersoftware", "monitoring"],
        },
        {
            "title": _("Servers"),
            "fields": ["server_set"],
            "wide": ["server_set"],
        },
        {
            "title": _("Tags"),
            "fields": ["tags"],
            "wide": ["tags"],
        },
    ]

    server_set = ModelMultipleChoiceField(
        label="Server",
        queryset=ServerModel.objects.all().order_by("-cluster", "hostname"),
    )

    def __init__(self, *args, **kwargs):
        """
        Set initial list of servers, since this is a reverse model relation,
        this is done manually here
        """
        super().__init__(*args, **kwargs)

        self.fields["server_set"].required = False
        self.fields["server_set"].queryset = filter_queryset_for_user(
            ServerModel.objects.all().order_by("-cluster", "hostname"), self.user
        )
        if self.instance and self.instance.pk:
            self.fields["server_set"].initial = (
                self.instance.server_set.all().values_list("id", flat=True)
            )
        else:
            self.fields["server_set"].initial = []

    class Meta(SMForm.Meta):
        model = Model


class FormDisabled(Form, SMFormDisabled):
    """Read-only variant; monitoring has a dedicated toggle in the header."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields.pop("monitoring", None)
        # The detail page renders the member servers as its own table.
        self.fields.pop("server_set", None)
        self.layout = self.build_layout()
