from django import forms

# from django.forms import TextInput # If we want/need to override
from taggit.forms import TagWidget


class SMForm(forms.ModelForm):
    class Meta:
        fields = "__all__"


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
