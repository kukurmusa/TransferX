from django import forms

from .models import Player


class PlayerForm(forms.ModelForm):
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user and hasattr(user, "club_profile"):
            self.fields["current_club"].queryset = self.fields["current_club"].queryset.filter(
                pk=user.club_profile.pk
            )

    class Meta:
        model = Player
        fields = ["name", "age", "nationality", "position", "current_club"]
