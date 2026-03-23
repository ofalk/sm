from django import forms
from .models import GroupProfile


class GroupProfileForm(forms.ModelForm):
    class Meta:
        model = GroupProfile
        fields = ["owner", "max_items", "max_users"]
