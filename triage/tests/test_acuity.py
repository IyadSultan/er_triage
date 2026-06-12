"""Unit tests for the deterministic acuity calculator."""
from django.test import SimpleTestCase

from triage.services.acuity import AcuityCalculator


def _vitals(hr=80, sbp=120, dbp=80, rr=16, spo2=98, temp_c=37.0):
    return {"hr": hr, "sbp": sbp, "dbp": dbp, "rr": rr, "spo2": spo2, "temp_c": temp_c}


class AcuityCalculatorTests(SimpleTestCase):
    def test_septic_shock_returns_1(self):
        acuity = AcuityCalculator.compute(_vitals(sbp=80), age=60, oncology={})
        self.assertEqual(acuity, 1)

    def test_febrile_neutropenia_returns_high_acuity(self):
        onc = {"on_chemotherapy": True, "neutropenia_known": True}
        acuity = AcuityCalculator.compute(_vitals(temp_c=39.2), age=58, oncology=onc)
        self.assertEqual(acuity, 1)  # temp>=39 + chemo + neutropenia -> acuity 1

    def test_febrile_on_chemo_returns_2(self):
        onc = {"on_chemotherapy": True, "neutropenia_known": False}
        acuity = AcuityCalculator.compute(_vitals(temp_c=38.3), age=50, oncology=onc)
        self.assertEqual(acuity, 2)

    def test_tachycardia_returns_3(self):
        acuity = AcuityCalculator.compute(_vitals(hr=130), age=40, oncology={})
        self.assertEqual(acuity, 3)

    def test_stable_adult_returns_5(self):
        acuity = AcuityCalculator.compute(_vitals(), age=30, oncology={})
        self.assertEqual(acuity, 5)

    def test_stable_elderly_returns_4(self):
        acuity = AcuityCalculator.compute(_vitals(), age=80, oncology={})
        self.assertEqual(acuity, 4)
