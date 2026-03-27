from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.providers.base import MemoProvider
from app.providers.mock_provider import MockMemoProvider
from app.providers.openai_provider import OpenAIMemoProvider
from app.repositories.triage_repo import TriageRepository
from app.schemas.models import IncidentBundle, TriageHistoryItem, TriageResult
from app.services.bundle_loader import BundleLoader
from app.services.evidence_retrieval import EvidenceRetrieval
from app.services.policy_engine import PolicyEngine
from app.services.scenario_classifier import ScenarioClassifier

logger = logging.getLogger(__name__)


class TriageService:
    def __init__(self, db: Session, settings: Optional[Settings] = None):
        self.settings = settings or get_settings()
        self.bundle_loader = BundleLoader()
        self.classifier = ScenarioClassifier()
        self.retrieval = EvidenceRetrieval()
        self.policy = PolicyEngine()
        self.repository = TriageRepository(db)
        self.memo_provider = self._select_provider()

    def assess_sample(self, sample_id: str) -> TriageResult:
        bundle = self.bundle_loader.load_sample(sample_id)
        return self.assess_bundle(bundle)

    def assess_bundle(self, bundle: IncidentBundle) -> TriageResult:
        scenario = self.classifier.classify(bundle)
        likely_service = self.classifier.detect_likely_service(bundle)
        evidence = self.retrieval.retrieve(bundle, scenario, likely_service)

        decision = self.policy.evaluate(bundle, scenario, likely_service, evidence)

        result = TriageResult(
            triage_id=str(uuid4()),
            incident_id=bundle.incident_id,
            scenario_type=scenario,
            likely_service=likely_service,
            likely_root_causes=decision.likely_root_causes,
            severity=decision.severity,
            escalation_target=decision.escalation_target,
            safe_next_actions=decision.safe_next_actions,
            evidence=evidence,
            missing_context=decision.missing_context,
            memo="",
            score=decision.score,
            created_at=datetime.now(timezone.utc),
        )

        memo = self.memo_provider.generate_memo(result)
        result = result.model_copy(update={"memo": memo})

        self.repository.save(
            bundle=bundle.model_dump(mode="json"),
            result=result.model_dump(mode="json"),
        )

        logger.info(
            "triage_completed",
            extra={
                "triage_id": result.triage_id,
                "incident_id": result.incident_id,
                "scenario_type": result.scenario_type.value,
                "severity": result.severity.value,
                "score": result.score,
            },
        )

        return result

    def assess_payload(self, payload: dict) -> TriageResult:
        bundle = self.bundle_loader.parse_bundle_payload(payload)
        return self.assess_bundle(bundle)

    def parse_upload(self, raw_bytes: bytes) -> IncidentBundle:
        return self.bundle_loader.parse_upload_bytes(raw_bytes)

    def get_triage(self, triage_id: str) -> Optional[TriageResult]:
        raw = self.repository.get_result(triage_id)
        if not raw:
            return None
        return TriageResult.model_validate(raw)

    def history(self, limit: int = 100) -> list[TriageHistoryItem]:
        items = self.repository.list_recent(limit=limit)
        return [
            TriageHistoryItem(
                triage_id=item["triage_id"],
                incident_id=item["incident_id"],
                scenario_type=item["scenario_type"],
                likely_service=item["likely_service"],
                severity=item["severity"],
                escalation_target=item["escalation_target"],
                score=item["score"],
                created_at=item["created_at"],
            )
            for item in items
        ]

    def list_samples(self) -> list[str]:
        return self.bundle_loader.list_sample_ids()

    def _select_provider(self) -> MemoProvider:
        mode = self.settings.provider_mode
        if mode == "mock":
            return MockMemoProvider()

        if mode == "openai":
            return OpenAIMemoProvider(self.settings)

        if self.settings.openai_api_key:
            try:
                return OpenAIMemoProvider(self.settings)
            except Exception:
                logger.exception("failed_to_initialize_openai_provider")

        return MockMemoProvider()
