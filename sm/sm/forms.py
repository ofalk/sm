from django import forms

# from django.forms import TextInput # If we want/need to override
from django.forms.models import ModelChoiceField, ModelMultipleChoiceField
from taggit.forms import TagWidget

from .mixins import filter_queryset_for_user


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
