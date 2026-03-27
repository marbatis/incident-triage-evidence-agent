from __future__ import annotations

import json
from pathlib import Path

from app.schemas.models import IncidentBundle
from app.services.evidence_retrieval import EvidenceRetrieval
from app.services.scenario_classifier import ScenarioClassifier


def _load_bundle(path: Path) -> IncidentBundle:
    return IncidentBundle.model_validate(json.loads(path.read_text(encoding="utf-8")))


def test_retrieval_returns_grounded_citations(sample_dir: Path) -> None:
    bundle = _load_bundle(sample_dir / "cert_expiry_auth_service.json")
    classifier = ScenarioClassifier()
    scenario = classifier.classify(bundle)
    service = classifier.detect_likely_service(bundle)

    evidence = EvidenceRetrieval().retrieve(bundle, scenario, service)

    citation_ids = {item.citation_id for item in evidence}
    assert any(citation.startswith("ALERT:") for citation in citation_ids)
    assert any(citation.startswith("LOG:") for citation in citation_ids)
    assert any(citation.startswith("RUNBOOK:") for citation in citation_ids)
