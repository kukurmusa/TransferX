from django import forms
from django.utils import timezone

from .models import Auction, Bid


class AuctionForm(forms.ModelForm):
    deadline = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}),
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            self.fields["player"].queryset = self.fields["player"].queryset.filter(
                created_by=user
            )

    class Meta:
        model = Auction
        fields = ["player", "deadline", "reserve_price", "min_increment"]

    def clean_deadline(self):
        deadline = self.cleaned_data["deadline"]
        if timezone.is_naive(deadline):
            deadline = timezone.make_aware(deadline, timezone.get_current_timezone())
        if deadline <= timezone.now():
            raise forms.ValidationError("Deadline must be in the future")
        return deadline


class BidForm(forms.ModelForm):
    wage_offer_weekly = forms.DecimalField(min_value=0, required=True)

    class Meta:
        model = Bid
        fields = ["amount", "wage_offer_weekly", "notes"]

    def clean_amount(self):
        amount = self.cleaned_data["amount"]
        if amount <= 0:
            raise forms.ValidationError("Bid amount must be positive")
        return amount
