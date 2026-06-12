"""View / end-to-end tests.

These use Django's test client and a real (SQLite) test database. The LLM call is
patched so the tests never touch the network.
"""
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from triage.models import Patient, TriageEvent


def _payload(**overrides):
    base = {
        "mrn": "999888777",
        "name": "Test Patient",
        "age": 58,
        "sex": "F",
        "chief_complaint": "Fever 39.4 for 6 hours, last chemo 9 days ago.",
        "heart_rate": 118,
        "systolic_bp": 102,
        "diastolic_bp": 64,
        "respiratory_rate": 22,
        "spo2": 95,
        "temperature_c": "39.4",
        "known_malignancy": "yes",
        "on_chemotherapy": "yes",
        "days_since_last_cycle": 9,
        "neutropenia_known": "yes",
    }
    base.update(overrides)
    return base


class NurseFormViewTests(TestCase):
    def test_get_renders_form(self):
        response = self.client.get(reverse("nurse_form"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Chief complaint")

    @patch("triage.views.OncologicEmergencyExtractor")
    def test_post_creates_event_and_redirects(self, mock_extractor):
        mock_extractor.return_value.extract.return_value = (["neutropenic_fever"], "ok")

        response = self.client.post(reverse("nurse_form"), _payload())

        self.assertEqual(response.status_code, 302)
        event = TriageEvent.objects.get()
        self.assertIn(event.acuity, (1, 2))
        self.assertIn("neutropenic_fever", event.oncologic_emergency_flags)
        self.assertEqual(event.extractor_status, "ok")
        # PHI protection: the raw MRN is not what's stored.
        self.assertNotEqual(event.patient.mrn_encoded, "999888777")
        # ...but it round-trips back to the patient name through Fernet.
        self.assertEqual(event.patient.name, "Test Patient")

    def test_post_rejects_out_of_range_vitals(self):
        response = self.client.post(reverse("nurse_form"), _payload(spo2=5))
        self.assertEqual(response.status_code, 200)  # re-renders, no redirect
        self.assertEqual(TriageEvent.objects.count(), 0)


class QueueAndDetailTests(TestCase):
    @patch("triage.views.OncologicEmergencyExtractor")
    def test_queue_shows_submitted_patient(self, mock_extractor):
        mock_extractor.return_value.extract.return_value = ([], "ok")
        self.client.post(reverse("nurse_form"), _payload(chief_complaint="ankle sprain"))

        response = self.client.get(reverse("doctor_queue"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Patient.objects.count(), 1)
