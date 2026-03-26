"""
VYTALYOU™ Stage 3: LLM Engine
OpenAI GPT-4 integration for longevity report and physician sheet generation.
"""

import json
import logging
import os
from typing import Tuple

from openai import AsyncOpenAI
from dotenv import load_dotenv

from models.schemas import (
    ExtractedPatientData, DerivedMetrics,
    LongevityReport, PhysicianSheet,
    PhysicianFinding,
)
from prompts.longevity_report import (
    LONGEVITY_REPORT_SYSTEM_PROMPT,
    LONGEVITY_REPORT_USER_PROMPT_TEMPLATE,
)
from prompts.physician_sheet import (
    PHYSICIAN_SHEET_SYSTEM_PROMPT,
    PHYSICIAN_SHEET_USER_PROMPT,
)

load_dotenv()


class LLMEngine:
    """Handles all LLM interactions for the longevity analysis pipeline."""

    def __init__(self):
        self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o")

    def _serialize_data(self, data: ExtractedPatientData, metrics: DerivedMetrics) -> dict:
        """Prepare data for prompt injection, filtering None values."""
        def clean(obj):
            if hasattr(obj, "model_dump"):
                d = obj.model_dump()
            elif isinstance(obj, dict):
                d = obj
            else:
                return str(obj)
            return {k: v for k, v in d.items() if v is not None}

        return {
            "patient_json": json.dumps(clean(data.patient), indent=2),
            "labs_json": json.dumps(clean(data.labs), indent=2),
            "lipids_json": json.dumps(clean(data.lipids), indent=2),
            "liver_json": json.dumps(clean(data.liver), indent=2),
            "inflammation_json": json.dumps(clean(data.inflammation), indent=2),
            "inbody_json": json.dumps(clean(data.inbody), indent=2),
            "cardiac_json": json.dumps(clean(data.cardiac), indent=2),
            "derived_json": json.dumps(clean(metrics), indent=2),
            "raw_text": data.raw_text,
        }

    async def generate_longevity_report(
        self,
        data: ExtractedPatientData,
        metrics: DerivedMetrics
    ) -> LongevityReport:
        """Generate the Ultra Precision Longevity Report via GPT-4 in Markdown format."""
        serialized = self._serialize_data(data, metrics)

        # Log raw text length and extracted data for debugging
        logging.info(f"[LLM] Raw text length: {len(serialized.get('raw_text', ''))} chars")
        logging.info(f"[LLM] Patient JSON: {serialized.get('patient_json', 'N/A')[:200]}")
        logging.info(f"[LLM] Labs JSON: {serialized.get('labs_json', 'N/A')[:200]}")

        system_prompt = LONGEVITY_REPORT_SYSTEM_PROMPT.format(**serialized)
        user_prompt = LONGEVITY_REPORT_USER_PROMPT_TEMPLATE

        logging.info(f"[LLM] System prompt length: {len(system_prompt)} chars")

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.4,
            max_tokens=16000
        )

        raw = response.choices[0].message.content
        logging.info(f"[LLM] Report response length: {len(raw or '')} chars")

        if not raw or len(raw.strip()) < 100:
            logging.error(f"[LLM] Empty or too-short response received! Response: {raw}")

        # Parse into the structured model
        return LongevityReport(markdown=raw)

    async def generate_physician_sheet(
        self,
        data: ExtractedPatientData,
        metrics: DerivedMetrics,
        report: LongevityReport,
    ) -> PhysicianSheet:
        """Generate the Physician Interpretation Sheet via GPT-4."""
        serialized = self._serialize_data(data, metrics)
        
        # We no longer extract strict integers from LongevityReport since the user explicitly requested raw continuous Markdown
        serialized["longevity_score"] = "Derived from Markdown Text"
        serialized["biological_age"] = str(metrics.estimated_biological_age or 0)
        serialized["biological_age_drift"] = str(metrics.biological_age_drift or 0)

        user_prompt = PHYSICIAN_SHEET_USER_PROMPT.format(**serialized)

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": PHYSICIAN_SHEET_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
            max_tokens=3000,
            response_format={"type": "json_object"},
        )

        raw = response.choices[0].message.content
        sheet_data = json.loads(raw)

        return PhysicianSheet(
            patient_summary=sheet_data.get("patient_summary", ""),
            findings=[
                PhysicianFinding(**f) for f in sheet_data.get("findings", [])
            ],
            priorities=sheet_data.get("priorities", []),
            follow_up_timeline=sheet_data.get("follow_up_timeline", ""),
        )

    async def generate_full_analysis(
        self,
        data: ExtractedPatientData,
        metrics: DerivedMetrics,
    ) -> Tuple[LongevityReport, PhysicianSheet]:
        """Generate both the longevity report and physician sheet."""
        report = await self.generate_longevity_report(data, metrics)
        physician_sheet = await self.generate_physician_sheet(data, metrics, report)
        return report, physician_sheet


# Singleton
llm_engine = LLMEngine()
