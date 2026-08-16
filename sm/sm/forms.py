from django import forms

# from django.forms import TextInput # If we want/need to override
from django.forms.models import ModelChoiceField, ModelMultipleChoiceField
from taggit.forms import TagWidget

from .mixins import filter_queryset_for_user
from django.utils.translation import gettext as _


class SMForm(forms.ModelForm):
    """
    Base model form. Accepts a ``user`` kwarg so FK choice fields are scoped to
    the user's accessible groups (prevents a user from referencing another
    tenant's related objects through the web UI).
    """

    class Meta:
        fields = "__all__"

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        self.scope_querysets()

    def scope_querysets(self):
        for field in self.fields.values():
            if isinstance(field, (ModelChoiceField, ModelMultipleChoiceField)):
                model = getattr(field.queryset, "model", None)
                if model is not None and hasattr(model, "group"):
                    field.queryset = filter_queryset_for_user(field.queryset, self.user)


class UniquePerGroupMixin:
    """
    Enforces name uniqueness per scope at the form level. The scope is the
    instance's group (pre-assigned by ``MultiTenantMixin.get_form``) or the
    single global scope when the group is null. The DB UniqueConstraint
    ``(name, group)`` treats NULL rows as always distinct, so this check is
    needed to prevent duplicate *global* items.
    """

    #: Model fields that must be unique together within a scope.
    unique_fields: tuple = ("name",)

    def clean(self):
        cleaned_data = super().clean()
        values = [cleaned_data.get(f) for f in self.unique_fields]
        if any(v is None or v == "" for v in values):
            return cleaned_data
        model = self.Meta.model
        lookup = {f: cleaned_data.get(f) for f in self.unique_fields}
        group = getattr(self.instance, "group_id", None)
        if group:
            lookup["group"] = group
        qs = model.objects.filter(**lookup)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            self.add_error(
                "name",
                _("An item with this name already exists in this scope."),
            )
        return cleaned_data


class BulkActionForm(forms.Form):
    """
    Generic bulk-action form used by the shared list templates. Subclasses can
    add extra fields (e.g. a status dropdown for models with a status FK).
    """

    delete = forms.BooleanField(required=False, label=_("Delete selected items"))


class SMFormDisabled(SMForm):
    """
    Form for the detail view, disables all user input
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = getattr(self, "instance", None)
        if instance and instance.pk:
            for field in self.fields:
                if self.fields[field].widget.__class__ is not TagWidget:
                    # self.fields[field].widget = TextInput()
                    pass  # No logic for this atm
                self.fields[field].widget.attrs["disabled"] = True

    class Meta(SMForm.Meta):
        pass
