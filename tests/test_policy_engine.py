from __future__ import annotations

import json
from pathlib import Path

from app.schemas.models import IncidentBundle, ScenarioType, Severity
from app.services.evidence_retrieval import EvidenceRetrieval
from app.services.policy_engine import PolicyEngine
from app.services.scenario_classifier import ScenarioClassifier


def _load_bundle(path: Path) -> IncidentBundle:
    return IncidentBundle.model_validate(json.loads(path.read_text(encoding="utf-8")))


def _evaluate(path: Path) -> tuple[ScenarioType, Severity, str]:
    bundle = _load_bundle(path)
    classifier = ScenarioClassifier()
    scenario = classifier.classify(bundle)
    service = classifier.detect_likely_service(bundle)
    evidence = EvidenceRetrieval().retrieve(bundle, scenario, service)
    decision = PolicyEngine().evaluate(bundle, scenario, service, evidence)
    return scenario, decision.severity, decision.escalation_target


def test_certificate_issue_escalates_to_incident_commander(sample_dir: Path) -> None:
    scenario, severity, target = _evaluate(sample_dir / "cert_expiry_auth_service.json")
    assert scenario == ScenarioType.CERTIFICATE_ISSUE
    assert severity == Severity.SEV1
    assert target == "incident_commander_oncall"


def test_retry_storm_is_service_owner_escalation(sample_dir: Path) -> None:
    scenario, severity, target = _evaluate(sample_dir / "retry_storm_payments.json")
    assert scenario == ScenarioType.RETRY_STORM
    assert severity == Severity.SEV2
    assert target == "service_owner_oncall"


def test_dependency_outage_high_severity(sample_dir: Path) -> None:
    scenario, severity, target = _evaluate(sample_dir / "dependency_outage_notifications.json")
    assert scenario == ScenarioType.DEPENDENCY_OUTAGE
    assert severity == Severity.SEV1
    assert target == "incident_commander_oncall"
