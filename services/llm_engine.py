"""
VYTALYOU™ Stage 3: LLM Engine
Multi-provider support: OpenAI GPT-4 + Anthropic Claude.
"""

import asyncio
import json
import logging
import os
import re
from typing import Tuple, Optional

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
from prompts.claude_structured_report import (
    CLAUDE_REPORT_PART_A_SYSTEM,
    CLAUDE_REPORT_PART_A_USER,
    CLAUDE_REPORT_PART_B_SYSTEM,
    CLAUDE_REPORT_PART_B_USER,
)
from prompts.physician_sheet import (
    PHYSICIAN_SHEET_SYSTEM_PROMPT,
    PHYSICIAN_SHEET_USER_PROMPT,
)

load_dotenv()

logger = logging.getLogger(__name__)

# ─── Available Models ────────────────────────────────────────────────────────
AVAILABLE_MODELS = {
    # OpenAI
    "gpt-4o":             {"provider": "openai", "label": "GPT-4o"},
    "gpt-4o-mini":        {"provider": "openai", "label": "GPT-4o Mini"},
    "gpt-4-turbo":        {"provider": "openai", "label": "GPT-4 Turbo"},
    # Anthropic Claude
    "claude-opus-4-5":    {"provider": "anthropic", "label": "Claude Opus 4.5"},
    "claude-sonnet-4-5":  {"provider": "anthropic", "label": "Claude Sonnet 4.5"},
    "claude-haiku-3-5":   {"provider": "anthropic", "label": "Claude Haiku 3.5"},
}

DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")


def get_provider(model_id: str) -> str:
    """Return 'openai' or 'anthropic' for a given model id."""
    info = AVAILABLE_MODELS.get(model_id)
    if info:
        return info["provider"]
    # Fallback heuristic
    if model_id.startswith("claude"):
        return "anthropic"
    return "openai"


class LLMEngine:
    """Handles all LLM interactions for the longevity analysis pipeline.
    Supports OpenAI and Anthropic Claude models transparently.
    """

    def __init__(self):
        # Lazy-init clients — only import/create if key is present
        self._openai_client = None
        self._anthropic_client = None

    def _get_openai(self):
        if self._openai_client is None:
            from openai import AsyncOpenAI
            self._openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        return self._openai_client

    def _get_anthropic(self):
        if self._anthropic_client is None:
            import anthropic
            self._anthropic_client = anthropic.AsyncAnthropic(
                api_key=os.getenv("ANTHROPIC_API_KEY")
            )
        return self._anthropic_client

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
            "patient_json":    json.dumps(clean(data.patient), indent=2),
            "labs_json":       json.dumps(clean(data.labs), indent=2),
            "lipids_json":     json.dumps(clean(data.lipids), indent=2),
            "liver_json":      json.dumps(clean(data.liver), indent=2),
            "inflammation_json": json.dumps(clean(data.inflammation), indent=2),
            "inbody_json":     json.dumps(clean(data.inbody), indent=2),
            "cardiac_json":    json.dumps(clean(data.cardiac), indent=2),
            "derived_json":    json.dumps(clean(metrics), indent=2),
            "raw_text":        data.raw_text,
        }

    # ─── OpenAI Calls ────────────────────────────────────────────────────────

    async def _openai_chat(
        self,
        model: str,
        system: str,
        user: str,
        max_tokens: int = 16384,
        temperature: float = 0.3,
        json_mode: bool = False,
    ) -> str:
        client = self._get_openai()
        kwargs = dict(
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        response = await client.chat.completions.create(**kwargs)
        return response.choices[0].message.content or ""

    # ─── Anthropic Calls ─────────────────────────────────────────────────────

    async def _anthropic_chat(
        self,
        model: str,
        system: str,
        user: str,
        max_tokens: int = 4096,
        temperature: float = 0.3,
        json_mode: bool = False,
    ) -> str:
        """Call Anthropic Claude with automatic continuation on truncation.
        
        When the response hits max_tokens, the API returns stop_reason='max_tokens'
        and the text is cut off mid-stream. This method detects that and makes
        follow-up continuation calls, stitching the full response together.
        """
        client = self._get_anthropic()
        # Claude: system is a top-level param, not a message role
        if json_mode:
            system = system + "\n\nIMPORTANT: You MUST respond with ONLY valid JSON. No markdown, no explanation — pure JSON object only."

        messages = [{"role": "user", "content": user}]
        full_text = ""
        MAX_CONTINUATIONS = 5

        # Map friendly UI names to actual Anthropic API model IDs
        # Try multiple ID formats — Anthropic changed naming in 2025
        MODEL_ALIASES = {
            "claude-sonnet-4-5": [
                "claude-sonnet-4-5-20250514",
                "claude-4-5-sonnet",
                "claude-3-5-sonnet-20241022",
                "claude-3-5-sonnet-20240620",
            ],
            "claude-sonnet-3-5": [
                "claude-3-5-sonnet-20241022",
                "claude-3-5-sonnet-20240620",
            ],
            "claude-opus-4-5": [
                "claude-opus-4-5-20250514",
                "claude-3-opus-20240229",
            ],
            "claude-haiku-3-5": [
                "claude-haiku-3-5-20250514",
                "claude-3-5-haiku-20241022",
                "claude-3-haiku-20240307",
            ],
        }

        # Build the list of model IDs to try
        candidates = MODEL_ALIASES.get(model, [model])
        # Always try the raw model name first (it might be a valid alias already)
        if model not in candidates:
            candidates = [model] + candidates

        logger.info(f"[LLM] Anthropic model candidates: {candidates}")

        last_error = None
        for candidate_id in candidates:
            try:
                logger.info(f"[LLM] Trying Anthropic model: {candidate_id}")
                for attempt in range(MAX_CONTINUATIONS + 1):
                    response = await client.messages.create(
                        model=candidate_id,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        system=system,
                        messages=messages,
                    )
                    chunk = response.content[0].text if response.content else ""
                    full_text += chunk

                    # Check if the response completed naturally
                    if response.stop_reason != "max_tokens":
                        logger.info(f"[LLM] Anthropic response complete (model={candidate_id}, stop_reason={response.stop_reason}, total={len(full_text)} chars)")
                        return full_text

                    # Response was truncated — ask Claude to continue
                    logger.warning(f"[LLM] Anthropic response truncated at max_tokens (attempt {attempt+1}, {len(full_text)} chars so far). Continuing...")
                    messages.append({"role": "assistant", "content": chunk})
                    messages.append({"role": "user", "content": "Continue generating the JSON from exactly where you stopped. Do not repeat any previous content. Output only the remaining JSON text."})

                return full_text  # All continuations done

            except Exception as e:
                last_error = e
                logger.warning(f"[LLM] Model '{candidate_id}' failed: {type(e).__name__}: {e}")
                # Reset state for next candidate
                full_text = ""
                messages = [{"role": "user", "content": user}]
                continue

        # All candidates failed
        error_msg = f"All Anthropic model IDs failed. Last error: {last_error}"
        logger.error(f"[LLM] {error_msg}")
        raise Exception(error_msg)


    # ─── Unified Dispatcher ──────────────────────────────────────────────────

    async def _chat(
        self,
        model: str,
        system: str,
        user: str,
        max_tokens: int = 16384,
        temperature: float = 0.3,
        json_mode: bool = False,
    ) -> str:
        provider = get_provider(model)
        if provider == "anthropic":
            return await self._anthropic_chat(model, system, user, max_tokens, temperature, json_mode)
        else:
            return await self._openai_chat(model, system, user, max_tokens, temperature, json_mode)

    # ─── Helpers ──────────────────────────────────────────────────────────────

    @staticmethod
    def _clean_json_text(raw: str) -> str:
        """Strip markdown fences and trailing commas from JSON text."""
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("```", 2)[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.rstrip("`").strip()
        # Remove trailing commas before } or ]
        raw = re.sub(r',\s*([\]}])', r'\1', raw)
        return raw

    # ─── Report Generation ───────────────────────────────────────────────────

    async def generate_longevity_report(
        self,
        data: ExtractedPatientData,
        metrics: DerivedMetrics,
        model: Optional[str] = None,
    ) -> LongevityReport:
        """Generate the Ultra Precision Longevity Report.
        
        For Anthropic: splits into 2 parallel API calls (Part A + Part B) to
        stay within output token limits, then merges the results.
        For OpenAI: uses the existing single-call markdown approach.
        """
        model = model or DEFAULT_MODEL
        provider = get_provider(model)
        serialized = self._serialize_data(data, metrics)

        logger.info(f"[LLM] Generating report with model: {model} (provider: {provider})")
        logger.info(f"[LLM] Raw text length: {len(serialized.get('raw_text', ''))} chars")

        if provider == "anthropic":
            # ── Split into 2 parallel calls ───────────────────────────────
            system_a = CLAUDE_REPORT_PART_A_SYSTEM.format(**serialized)
            system_b = CLAUDE_REPORT_PART_B_SYSTEM.format(**serialized)

            logger.info("[LLM] Anthropic: launching Part A + Part B in parallel")

            raw_a, raw_b = await asyncio.gather(
                self._chat(model=model, system=system_a, user=CLAUDE_REPORT_PART_A_USER,
                           max_tokens=4096, temperature=0.3, json_mode=True),
                self._chat(model=model, system=system_b, user=CLAUDE_REPORT_PART_B_USER,
                           max_tokens=4096, temperature=0.3, json_mode=True),
            )

            logger.info(f"[LLM] Part A: {len(raw_a)} chars, Part B: {len(raw_b)} chars")

            # Parse and merge
            raw_a = self._clean_json_text(raw_a)
            raw_b = self._clean_json_text(raw_b)

            try:
                part_a = json.loads(raw_a)
                part_b = json.loads(raw_b)
                merged = {**part_a, **part_b}
                raw = json.dumps(merged)
                logger.info(f"[LLM] Merged JSON: {len(raw)} chars, {len(merged)} top-level keys")
            except json.JSONDecodeError as e:
                logger.error(f"[LLM] JSON merge failed: {e}")
                logger.error(f"[LLM] Part A preview: {raw_a[:200]}")
                logger.error(f"[LLM] Part B preview: {raw_b[:200]}")
                # Return the raw text so the error handler in main.py can show it
                raw = raw_a

        else:
            system_prompt = LONGEVITY_REPORT_SYSTEM_PROMPT.format(**serialized)
            user_prompt = LONGEVITY_REPORT_USER_PROMPT_TEMPLATE
            
            raw = await self._chat(
                model=model,
                system=system_prompt,
                user=user_prompt,
                max_tokens=16000,
                temperature=0.3,
            )

        logger.info(f"[LLM] Report response length: {len(raw)} chars")
        if len(raw.strip()) < 100:
            logger.error(f"[LLM] Empty or too-short response! Response: {raw}")

        return LongevityReport(markdown=raw)

    async def generate_physician_sheet(
        self,
        data: ExtractedPatientData,
        metrics: DerivedMetrics,
        report: LongevityReport,
        model: Optional[str] = None,
    ) -> PhysicianSheet:
        """Generate the Physician Interpretation Sheet."""
        model = model or DEFAULT_MODEL
        serialized = self._serialize_data(data, metrics)

        serialized["longevity_score"] = "Derived from Markdown Text"
        serialized["biological_age"] = str(metrics.estimated_biological_age or 0)
        serialized["biological_age_drift"] = str(metrics.biological_age_drift or 0)

        user_prompt = PHYSICIAN_SHEET_USER_PROMPT.format(**serialized)

        raw = await self._chat(
            model=model,
            system=PHYSICIAN_SHEET_SYSTEM_PROMPT,
            user=user_prompt,
            max_tokens=3000,
            temperature=0.2,
            json_mode=True,
        )

        # Claude may sometimes wrap JSON in ```json ... ``` — strip that
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("```", 2)[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.rstrip("`").strip()

        sheet_data = json.loads(raw)
        return PhysicianSheet(
            patient_summary=sheet_data.get("patient_summary", ""),
            findings=[PhysicianFinding(**f) for f in sheet_data.get("findings", [])],
            priorities=sheet_data.get("priorities", []),
            follow_up_timeline=sheet_data.get("follow_up_timeline", ""),
        )

    async def generate_full_analysis(
        self,
        data: ExtractedPatientData,
        metrics: DerivedMetrics,
        model: Optional[str] = None,
    ) -> Tuple[LongevityReport, PhysicianSheet]:
        """Generate both the longevity report and physician sheet."""
        model = model or DEFAULT_MODEL
        report = await self.generate_longevity_report(data, metrics, model=model)
        physician_sheet = await self.generate_physician_sheet(data, metrics, report, model=model)
        return report, physician_sheet


# Singleton
llm_engine = LLMEngine()
