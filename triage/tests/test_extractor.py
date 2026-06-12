"""Unit tests for the oncologic emergency extractor.

No test hits the network. We assert the two behaviours that matter clinically:
  * with no API key, the extractor degrades gracefully (no crash);
  * a mocked LLM response is filtered to the closed set of valid flags.
"""
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from triage.services.oncologic_emergency import OncologicEmergencyExtractor


class ExtractorTests(SimpleTestCase):
    def test_no_api_key_degrades_gracefully(self):
        extractor = OncologicEmergencyExtractor()
        extractor.api_key = None
        flags, status = extractor.extract("fever and chills", {"on_chemotherapy": True})
        self.assertEqual(flags, [])
        self.assertEqual(status, "failed")

    def test_invalid_labels_are_dropped(self):
        extractor = OncologicEmergencyExtractor()
        extractor.api_key = "test-key"

        fake_message = MagicMock()
        fake_message.content = '{"flags": ["neutropenic_fever", "made_up_label"]}'
        fake_response = MagicMock()
        fake_response.choices = [MagicMock(message=fake_message)]

        fake_client = MagicMock()
        fake_client.chat.completions.create.return_value = fake_response

        with patch("openai.OpenAI", return_value=fake_client):
            flags, status = extractor.extract("febrile, on chemo", {"on_chemotherapy": True})

        self.assertEqual(status, "ok")
        self.assertIn("neutropenic_fever", flags)
        self.assertNotIn("made_up_label", flags)

    def test_exception_during_call_degrades(self):
        extractor = OncologicEmergencyExtractor()
        extractor.api_key = "test-key"
        fake_client = MagicMock()
        fake_client.chat.completions.create.side_effect = RuntimeError("network down")
        with patch("openai.OpenAI", return_value=fake_client):
            flags, status = extractor.extract("anything", {})
        self.assertEqual(flags, [])
        self.assertEqual(status, "failed")
