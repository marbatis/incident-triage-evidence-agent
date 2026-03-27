from __future__ import annotations

from pathlib import Path
from typing import Optional

from app.schemas.models import IncidentBundle, RetrievedEvidence, ScenarioType


class EvidenceRetrieval:
    SCENARIO_TERMS: dict[ScenarioType, set[str]] = {
        ScenarioType.CERTIFICATE_ISSUE: {"cert", "certificate", "x509", "tls", "expiry", "expired"},
        ScenarioType.RETRY_STORM: {"retry", "timeout", "429", "backoff", "throttle", "queue"},
        ScenarioType.DEPENDENCY_OUTAGE: {
            "dependency",
            "downstream",
            "unavailable",
            "connection",
            "dns",
            "saturation",
            "5xx",
        },
        ScenarioType.UNKNOWN: {"incident", "error", "failure"},
    }

    def __init__(self, data_dir: Optional[Path] = None):
        root = Path(__file__).resolve().parents[2]
        self.runbooks_dir = (data_dir or root / "data") / "runbooks"

    def retrieve(
        self,
        bundle: IncidentBundle,
        scenario_type: ScenarioType,
        likely_service: str,
    ) -> list[RetrievedEvidence]:
        candidates: list[RetrievedEvidence] = []

        for idx, alert in enumerate(bundle.alerts, start=1):
            excerpt = f"{alert.name}: {alert.message}"
            score = self._score(excerpt, scenario_type, likely_service)
            if score > 0:
                candidates.append(
                    RetrievedEvidence(
                        source_type="alert",
                        source_name=alert.name,
                        excerpt=excerpt,
                        relevance_score=score,
                        citation_id=f"ALERT:{idx}",
                    )
                )

        for idx, metric in enumerate(bundle.metric_snapshots, start=1):
            excerpt = f"{metric.metric_name}={metric.value}"
            score = self._score(excerpt, scenario_type, likely_service)
            if score > 0:
                candidates.append(
                    RetrievedEvidence(
                        source_type="metric",
                        source_name=metric.metric_name,
                        excerpt=excerpt,
                        relevance_score=score,
                        citation_id=f"METRIC:{idx}",
                    )
                )

        for idx, log in enumerate(bundle.logs, start=1):
            score = self._score(log.message, scenario_type, likely_service)
            if score > 0:
                candidates.append(
                    RetrievedEvidence(
                        source_type="log",
                        source_name=log.level,
                        excerpt=log.message,
                        relevance_score=score,
                        citation_id=f"LOG:{idx}",
                    )
                )

        for idx, change in enumerate(bundle.recent_changes, start=1):
            score = self._score(change.summary, scenario_type, likely_service)
            if score > 0:
                candidates.append(
                    RetrievedEvidence(
                        source_type="change",
                        source_name=change.change_id,
                        excerpt=change.summary,
                        relevance_score=score,
                        citation_id=f"CHANGE:{idx}",
                    )
                )

        for path in self._candidate_runbooks(bundle, likely_service):
            if not path.exists():
                continue
            lines = path.read_text(encoding="utf-8").splitlines()
            for line_no, line in enumerate(lines, start=1):
                clean = line.strip()
                if not clean:
                    continue
                score = self._score(clean, scenario_type, likely_service)
                if score < 0.4:
                    continue
                candidates.append(
                    RetrievedEvidence(
                        source_type="runbook",
                        source_name=path.name,
                        excerpt=clean,
                        relevance_score=min(score, 1.0),
                        citation_id=f"RUNBOOK:{path.name}#L{line_no}",
                    )
                )

        candidates.sort(key=lambda item: item.relevance_score, reverse=True)
        return candidates[:20]

    def _candidate_runbooks(self, bundle: IncidentBundle, likely_service: str) -> list[Path]:
        names: set[str] = set()

        for ref in bundle.runbook_refs:
            stem = Path(ref).name
            if not stem.endswith(".md"):
                stem += ".md"
            names.add(stem)

        if likely_service != "unknown_service":
            names.add(f"{likely_service}.md")

        if not names:
            names.update(path.name for path in self.runbooks_dir.glob("*.md"))

        return [self.runbooks_dir / name for name in sorted(names)]

    def _score(self, text: str, scenario_type: ScenarioType, likely_service: str) -> float:
        score = 0.0
        lowered = text.lower()

        terms = self.SCENARIO_TERMS.get(scenario_type, set())
        matches = sum(1 for term in terms if term in lowered)
        if matches:
            score += min(matches * 0.2, 0.8)

        if likely_service and likely_service.lower() in lowered:
            score += 0.2

        return min(score, 1.0)
