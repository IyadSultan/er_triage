"""Seed the queue with a handful of fake patients.

Run `python manage.py seed_demo` so the doctor queue (and the Lesson 6 dashboard)
have something to show without anyone having to type into the form — and without
needing an OpenAI key. The flags here are hand-set, not LLM-generated.
"""
from django.core.management.base import BaseCommand

from triage.models import Patient, TriageEvent
from triage.services.acuity import AcuityCalculator

DEMO = [
    # (mrn, name, age, sex, complaint, vitals, oncology, flags)
    ("1001", "Aisha N.", 61, "F", "Fever 39.5, last chemo 8 days ago, feels weak.",
     {"hr": 122, "sbp": 96, "dbp": 60, "rr": 24, "spo2": 94, "temp_c": 39.5},
     {"known_malignancy": True, "on_chemotherapy": True, "days_since_last_cycle": 8, "neutropenia_known": True},
     ["neutropenic_fever"]),
    ("1002", "Omar K.", 54, "M", "New severe back pain, legs feel weak since morning.",
     {"hr": 88, "sbp": 134, "dbp": 82, "rr": 16, "spo2": 98, "temp_c": 37.1},
     {"known_malignancy": True, "on_chemotherapy": False, "days_since_last_cycle": None, "neutropenia_known": False},
     ["cord_compression"]),
    ("1003", "Lina H.", 47, "F", "Twisted ankle on stairs, mild swelling.",
     {"hr": 78, "sbp": 120, "dbp": 78, "rr": 14, "spo2": 99, "temp_c": 36.9},
     {"known_malignancy": False, "on_chemotherapy": False, "days_since_last_cycle": None, "neutropenia_known": False},
     []),
    ("1004", "Yousef D.", 69, "M", "Confused, very thirsty, constipated for days.",
     {"hr": 96, "sbp": 128, "dbp": 80, "rr": 18, "spo2": 97, "temp_c": 37.2},
     {"known_malignancy": True, "on_chemotherapy": False, "days_since_last_cycle": None, "neutropenia_known": False},
     ["hypercalcemia_of_malignancy"]),
    ("1005", "Maya S.", 33, "F", "Sore throat, no fever, otherwise well.",
     {"hr": 72, "sbp": 118, "dbp": 76, "rr": 14, "spo2": 99, "temp_c": 37.0},
     {"known_malignancy": False, "on_chemotherapy": False, "days_since_last_cycle": None, "neutropenia_known": False},
     []),
]


class Command(BaseCommand):
    help = "Create a few demo triage events for the queue and dashboard."

    def handle(self, *args, **options):
        created = 0
        for mrn, name, age, sex, complaint, vitals, onc, flags in DEMO:
            patient = Patient.upsert(mrn, name, age, sex)
            acuity = AcuityCalculator.compute(vitals, age, onc)
            TriageEvent.objects.create(
                patient=patient,
                chief_complaint=complaint,
                vitals=vitals,
                oncology_context=onc,
                acuity=acuity,
                oncologic_emergency_flags=flags,
                extractor_status="ok",
            )
            created += 1
        self.stdout.write(self.style.SUCCESS(f"Seeded {created} demo triage events."))
