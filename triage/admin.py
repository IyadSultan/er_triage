from django.contrib import admin

from .models import Patient, TriageEvent


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    # Show only the encoded MRN — never the decrypted name — in list view.
    list_display = ("mrn_encoded", "age", "sex", "created_at")
    readonly_fields = ("mrn_encoded", "created_at")


@admin.register(TriageEvent)
class TriageEventAdmin(admin.ModelAdmin):
    list_display = ("id", "acuity", "extractor_status", "timestamp")
    list_filter = ("acuity", "extractor_status")
