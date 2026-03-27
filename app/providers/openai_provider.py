from __future__ import annotations

import json
import logging

from app.config import Settings
from app.providers.base import MemoProvider
from app.schemas.models import TriageResult

logger = logging.getLogger(__name__)


class OpenAIMemoProvider(MemoProvider):
    def __init__(self, settings: Settings):
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is not configured")

        try:
            from openai import OpenAI
        except Exception as exc:  # pragma: no cover
            raise RuntimeError("openai package is required for OpenAI provider") from exc

        self._client = OpenAI(api_key=settings.openai_api_key)
        self._model = settings.openai_model

    def generate_memo(self, result: TriageResult) -> str:
        payload = {
            "incident_id": result.incident_id,
            "scenario_type": result.scenario_type.value,
            "severity": result.severity.value,
            "likely_service": result.likely_service,
            "likely_root_causes": result.likely_root_causes,
            "safe_next_actions": result.safe_next_actions,
            "evidence": [ev.model_dump() for ev in result.evidence],
            "missing_context": result.missing_context,
            "escalation_target": result.escalation_target,
        }

        prompt = (
            "You are writing a grounded incident triage memo. "
            "Use only the provided evidence and never invent actions. "
            "Return 1 concise paragraph and include citation IDs in parentheses.\n\n"
            f"Deterministic triage data:\n{json.dumps(payload, indent=2)}"
        )

        try:
            response = self._client.responses.create(
                model=self._model,
                input=prompt,
            )
            text = getattr(response, "output_text", "")
            if text and text.strip():
                return text.strip()
        except Exception as exc:  # pragma: no cover
            logger.exception("openai_memo_generation_failed", extra={"error": str(exc)})

        return (
            f"Deterministic fallback memo: {result.incident_id} is {result.severity.value} "
            f"for {result.likely_service}; escalate to {result.escalation_target}."
        )
