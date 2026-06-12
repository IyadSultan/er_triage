"""Deterministic ESI-like acuity calculator.

A pure-Python class. No I/O, no network, no LLM. This is a hard rule from the
project: **the LLM never computes acuity** — acuity is arithmetic on vitals, and
arithmetic belongs in code you can unit-test and reason about, not in a model.

`compute()` returns an integer 1..5, where 1 is the sickest. The rule table is
intentionally simple and readable; a real deployment would tune it against the
unit's data and have it signed off by an attending.
"""
from __future__ import annotations


class AcuityCalculator:
    """Maps vitals + age + oncology context to an ESI-like acuity 1..5."""

    @staticmethod
    def compute(vitals: dict, age: int, oncology: dict) -> int:
        hr = vitals.get("hr")
        sbp = vitals.get("sbp")
        rr = vitals.get("rr")
        spo2 = vitals.get("spo2")
        temp = vitals.get("temp_c")

        on_chemo = bool(oncology.get("on_chemotherapy"))
        neutropenia = bool(oncology.get("neutropenia_known"))

        # --- Acuity 1: immediate life threat -------------------------------
        if (
            (sbp is not None and sbp < 90)
            or (spo2 is not None and spo2 < 88)
            or (rr is not None and rr > 30)
            or (temp is not None and temp >= 39 and on_chemo and neutropenia)
        ):
            return 1

        # --- Acuity 2: high risk, rule out febrile neutropenia -------------
        if (
            (temp is not None and temp >= 38 and on_chemo)
            or (sbp is not None and 90 <= sbp <= 100)
            or (spo2 is not None and 88 <= spo2 <= 92)
        ):
            return 2

        # --- Acuity 3: concerning vitals -----------------------------------
        if (
            (hr is not None and hr > 120)
            or (rr is not None and 22 <= rr <= 30)
            or (temp is not None and 37.5 <= temp <= 37.9)
        ):
            return 3

        # --- Acuity 4 vs 5: stable; age is a tiebreaker --------------------
        if age is not None and (age >= 75 or age <= 1):
            return 4
        return 5
