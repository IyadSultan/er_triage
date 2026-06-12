"""Views for the ER Triage Extractor.

Four screens:
  * nurse_form_view        — GET shows the form; POST validates, scores, extracts, saves.
  * triage_confirmation_view — read-only "what just happened" page for the nurse.
  * doctor_queue_view      — the live queue, sickest first, emergencies flagged.
  * patient_detail_view    — one triage event in full, for the on-call attending.
"""
from __future__ import annotations

from django.shortcuts import get_object_or_404, redirect, render

from .forms import NurseTriageForm
from .models import Patient, TriageEvent
from .services.acuity import AcuityCalculator
from .services.oncologic_emergency import OncologicEmergencyExtractor


def nurse_form_view(request):
    if request.method == "POST":
        form = NurseTriageForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data

            vitals = {
                "hr": cd["heart_rate"],
                "sbp": cd["systolic_bp"],
                "dbp": cd["diastolic_bp"],
                "rr": cd["respiratory_rate"],
                "spo2": cd["spo2"],
                "temp_c": float(cd["temperature_c"]),
            }
            oncology = {
                "known_malignancy": cd["known_malignancy"] == "yes",
                "on_chemotherapy": cd["on_chemotherapy"] == "yes",
                "days_since_last_cycle": cd.get("days_since_last_cycle"),
                "neutropenia_known": cd["neutropenia_known"] == "yes",
            }

            # 1. Acuity — deterministic, never the LLM.
            acuity = AcuityCalculator.compute(vitals, cd["age"], oncology)

            # 2. Oncologic emergency flags — the LLM, with graceful degradation.
            flags, status = OncologicEmergencyExtractor().extract(cd["chief_complaint"], oncology)

            # 3. Upsert the patient (PHI protected in the model layer).
            patient = Patient.upsert(cd["mrn"], cd["name"], cd["age"], cd["sex"])

            # 4. Record the event.
            event = TriageEvent.objects.create(
                patient=patient,
                chief_complaint=cd["chief_complaint"],
                vitals=vitals,
                oncology_context=oncology,
                acuity=acuity,
                oncologic_emergency_flags=flags,
                extractor_status=status,
                audit_user=request.META.get("REMOTE_USER"),  # placeholder for v1
            )
            return redirect("triage_confirmation", event_id=event.pk)
    else:
        form = NurseTriageForm()

    return render(request, "triage/nurse_form.html", {"form": form})


def triage_confirmation_view(request, event_id):
    event = get_object_or_404(TriageEvent, pk=event_id)
    return render(request, "triage/triage_confirmation.html", {"event": event})


def doctor_queue_view(request):
    # Model Meta already orders by (acuity, timestamp): sickest, longest-waiting first.
    events = TriageEvent.objects.select_related("patient").all()
    return render(request, "triage/doctor_queue.html", {"events": events})


def patient_detail_view(request, event_id):
    event = get_object_or_404(TriageEvent.objects.select_related("patient"), pk=event_id)
    return render(request, "triage/patient_detail.html", {"event": event})
