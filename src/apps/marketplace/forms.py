import json

from django import forms

from .models import Offer


class OfferForm(forms.ModelForm):
    add_ons_raw = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 3}),
        help_text="Optional JSON for add-ons.",
        label="Add-ons (JSON)",
    )

    class Meta:
        model = Offer
        fields = [
            "fee_amount",
            "wage_weekly",
            "contract_years",
            "contract_end_date",
            "expires_at",
        ]
        widgets = {
            "expires_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "contract_end_date": forms.DateInput(attrs={"type": "date"}),
        }

    def clean_add_ons_raw(self):
        raw = self.cleaned_data.get("add_ons_raw")
        if not raw:
            return {}
        try:
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            raise forms.ValidationError("Add-ons must be valid JSON.") from exc


class OfferMessageForm(forms.Form):
    body = forms.CharField(widget=forms.Textarea(attrs={"rows": 3}))
