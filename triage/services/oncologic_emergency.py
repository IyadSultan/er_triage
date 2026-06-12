"""LLM extractor for oncologic emergencies.

Given a free-text chief complaint plus the structured oncology context, ask an
LLM which (if any) of four oncologic emergencies are suspected:

    neutropenic_fever, tumor_lysis, cord_compression, hypercalcemia_of_malignancy

Design rules baked in here:
  * **Closed set.** The model may only return labels from the four above. Anything
    else is dropped. This is the "JSON mode / structured output" discipline from
    earlier sessions — never trust free-form text into a clinical pipeline.
  * **Graceful degradation.** If there is no API key, the `openai` package isn't
    installed, or the call fails for any reason, we return `([], "failed")` and the
    caller still saves the triage row. A network blip must never lose a patient.
  * **Temperature 0.** Judgement should be as reproducible as the model allows.

The key is read from the OPENAI_API_KEY environment variable (a local .env in dev,
the Render dashboard in production). No key is committed, ever.
"""
from __future__ import annotations

import json
import logging
import os

logger = logging.getLogger("triage.oncologic_emergency")

VALID_FLAGS = {
    "neutropenic_fever",
    "tumor_lysis",
    "cord_compression",
    "hypercalcemia_of_malignancy",
}

_SYSTEM_PROMPT = """You are a triage decision-support assistant for an oncology ER.
Read the chief complaint and the structured oncology context. Decide which, if any,
of EXACTLY these four oncologic emergencies are suspected:

- neutropenic_fever: fever (>=38C) in a patient on chemotherapy, especially with
  known or possible neutropenia.
- tumor_lysis: features of tumor lysis syndrome (e.g., recent chemo for bulky/
  high-grade disease with weakness, palpitations, reduced urine, arrhythmia).
- cord_compression: new back pain with neurologic signs (leg weakness, numbness,
  bladder/bowel changes) in a patient with known malignancy.
- hypercalcemia_of_malignancy: confusion, constipation, polyuria, profound fatigue
  in a patient with known malignancy.

Respond with ONLY a JSON object of the form {"flags": [...]} where each element is
one of the four labels above. If none are suspected, return {"flags": []}.
Do not invent labels. Do not explain."""


class OncologicEmergencyExtractor:
    """Wraps a single LLM call behind a safe, closed-set interface."""

    def __init__(self, model: str | None = None):
        self.model = model or os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
        self.api_key = os.environ.get("OPENAI_API_KEY")

    def extract(self, chief_complaint: str, oncology_context: dict) -> tuple[list[str], str]:
        """Return (flags, status). status is 'ok' or 'failed'."""
        if not self.api_key:
            logger.info("no OPENAI_API_KEY set; skipping extraction (status=failed)")
            return ([], "failed")

        try:
            from openai import OpenAI
        except ImportError:
            logger.warning("openai package not installed; skipping extraction")
            return ([], "failed")

        user_payload = json.dumps(
            {"chief_complaint": chief_complaint, "oncology_context": oncology_context}
        )

        try:
            client = OpenAI(api_key=self.api_key)
            response = client.chat.completions.create(
                model=self.model,
                temperature=0,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": user_payload},
                ],
                timeout=10,
            )
            raw = response.choices[0].message.content or "{}"
            flags = json.loads(raw).get("flags", [])
            # Enforce the closed set — drop anything the model invented.
            clean = [f for f in flags if f in VALID_FLAGS]
            return (clean, "ok")
        except Exception as exc:  # noqa: BLE001 — degrade gracefully on ANY failure
            logger.warning("oncologic emergency extraction failed: %s", type(exc).__name__)
            return ([], "failed")
