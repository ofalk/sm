from django.utils.translation import gettext as _

from .models import Model
from sm.forms import SMForm, SMFormDisabled


class Form(SMForm):
    class Meta(SMForm.Meta):
        model = Model

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        kwargs["user"] = user  # let SMForm scope FK choices to the user
        super().__init__(*args, **kwargs)

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
    pass
