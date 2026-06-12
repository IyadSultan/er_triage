"""Data model for the ER Triage Extractor.

Two tables:
  * Patient — one row per person. The MRN is Optimus-encoded and the name is
    Fernet-encrypted (see triage/crypto.py). Raw PHI never sits here in the clear.
  * TriageEvent — one row per ER arrival. Holds the vitals, the oncology context,
    the computed acuity, and the LLM's emergency flags.
"""
from __future__ import annotations

from django.db import models

from .crypto import decrypt_name, encode_mrn, encrypt_name


class Patient(models.Model):
    mrn_encoded = models.CharField(max_length=40, unique=True, db_index=True)
    name_encrypted = models.BinaryField()
    age = models.IntegerField()
    sex = models.CharField(
        max_length=8,
        choices=[("M", "Male"), ("F", "Female"), ("Other", "Other")],
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    @property
    def name(self) -> str:
        """Decrypt the patient name on demand. Never store this; never log it."""
        return decrypt_name(self.name_encrypted)

    @classmethod
    def upsert(cls, mrn: str, name: str, age: int, sex: str) -> "Patient":
        """Create or update a patient, keyed by the Optimus-encoded MRN."""
        encoded = encode_mrn(mrn)
        patient, _created = cls.objects.update_or_create(
            mrn_encoded=encoded,
            defaults={
                "name_encrypted": encrypt_name(name),
                "age": age,
                "sex": sex,
            },
        )
        return patient

    def __str__(self) -> str:  # never expose the real name here
        return f"Patient<{self.mrn_encoded}>"


class TriageEvent(models.Model):
    EXTRACTOR_STATUS = [("ok", "ok"), ("failed", "failed"), ("timeout", "timeout")]

    patient = models.ForeignKey(Patient, on_delete=models.PROTECT, related_name="events")
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    chief_complaint = models.TextField(max_length=2000)
    vitals = models.JSONField(default=dict)  # {hr, sbp, dbp, rr, spo2, temp_c}
    oncology_context = models.JSONField(default=dict)  # {known_malignancy, ...}
    acuity = models.IntegerField(choices=[(i, str(i)) for i in range(1, 6)])
    oncologic_emergency_flags = models.JSONField(default=list)
    extractor_status = models.CharField(max_length=16, choices=EXTRACTOR_STATUS, default="ok")
    audit_user = models.CharField(max_length=80, null=True, blank=True)

    class Meta:
        # Doctor queue order: sickest first, then oldest-waiting first.
        ordering = ["acuity", "timestamp"]

    @property
    def has_emergency(self) -> bool:
        return bool(self.oncologic_emergency_flags)

    def __str__(self) -> str:
        return f"TriageEvent<{self.pk} acuity={self.acuity}>"
