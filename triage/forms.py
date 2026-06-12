"""The nurse triage form.

Server-side validation lives here: every numeric field has a clinical range, and
out-of-range values are rejected before anything touches the database or the LLM.
"""
from django import forms

YES_NO = [("yes", "Yes"), ("no", "No")]


class NurseTriageForm(forms.Form):
    # --- identity ----------------------------------------------------------
    mrn = forms.CharField(label="MRN", max_length=20)
    name = forms.CharField(label="Patient name", max_length=120)
    age = forms.IntegerField(label="Age", min_value=0, max_value=120)
    sex = forms.ChoiceField(
        label="Sex", choices=[("M", "Male"), ("F", "Female"), ("Other", "Other")]
    )

    # --- presentation ------------------------------------------------------
    chief_complaint = forms.CharField(
        label="Chief complaint", widget=forms.Textarea(attrs={"rows": 3}), max_length=2000
    )

    # --- vitals ------------------------------------------------------------
    heart_rate = forms.IntegerField(label="Heart rate", min_value=30, max_value=220)
    systolic_bp = forms.IntegerField(label="Systolic BP", min_value=40, max_value=300)
    diastolic_bp = forms.IntegerField(label="Diastolic BP", min_value=20, max_value=200)
    respiratory_rate = forms.IntegerField(label="Respiratory rate", min_value=5, max_value=60)
    spo2 = forms.IntegerField(label="SpO₂ (%)", min_value=50, max_value=100)
    temperature_c = forms.DecimalField(
        label="Temperature (°C)", min_value=30.0, max_value=43.0, max_digits=4, decimal_places=1
    )

    # --- oncology context --------------------------------------------------
    known_malignancy = forms.ChoiceField(label="Known malignancy", choices=YES_NO)
    on_chemotherapy = forms.ChoiceField(label="On chemotherapy", choices=YES_NO)
    days_since_last_cycle = forms.IntegerField(
        label="Days since last cycle", min_value=0, max_value=365, required=False
    )
    neutropenia_known = forms.ChoiceField(label="Neutropenia known", choices=YES_NO)

    def clean(self):
        cleaned = super().clean()
        # days_since_last_cycle is required only when the patient is on chemo.
        if cleaned.get("on_chemotherapy") == "yes" and cleaned.get("days_since_last_cycle") is None:
            self.add_error(
                "days_since_last_cycle",
                "Required when the patient is on chemotherapy.",
            )
        return cleaned
