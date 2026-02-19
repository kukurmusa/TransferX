from django import forms

from .models import PlayerInterest, Shortlist


class ShortlistForm(forms.ModelForm):
    class Meta:
        model = Shortlist
        fields = ["name", "description"]


class InterestForm(forms.Form):
    level = forms.ChoiceField(choices=PlayerInterest.Level.choices)
    stage = forms.ChoiceField(choices=PlayerInterest.Stage.choices, required=False)
    notes = forms.CharField(required=False, widget=forms.Textarea)
