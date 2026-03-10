from .models import Model
from sm.forms import SMForm, SMFormDisabled
from server.models import Model as ServerModel

from django.forms import ModelMultipleChoiceField


class Form(SMForm):
    """
    Form providing an extra field; All ServerModels ordered by cluster and
    hostname, additionally sets the initial list in __init__()
    """

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
        self.fields["server_set"].initial = self.instance.server_set.all().values_list(
            "id", flat=True
        )

    class Meta(SMForm.Meta):
        model = Model


class FormDisabled(Form, SMFormDisabled):
    pass
