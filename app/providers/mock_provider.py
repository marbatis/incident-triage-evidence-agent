from __future__ import annotations

from app.providers.base import MemoProvider
from app.schemas.models import TriageResult


class MockMemoProvider(MemoProvider):
    def generate_memo(self, result: TriageResult) -> str:
        risks = ", ".join(result.likely_root_causes[:2]) or "unknown root cause"
        top_evidence = "; ".join(ev.citation_id for ev in result.evidence[:3])
        actions = "; ".join(result.safe_next_actions[:3])
        missing = ", ".join(result.missing_context) if result.missing_context else "none"

        return (
            f"Incident {result.incident_id} is classified as {result.scenario_type.value} with "
            f"{result.severity.value} severity for {result.likely_service}. "
            f"Likely root causes: {risks}. "
            f"Escalate to {result.escalation_target}. "
            f"Safe next actions: {actions}. "
            f"Primary evidence: {top_evidence}. Missing context: {missing}."
        )
