from __future__ import annotations

import json
from pathlib import Path

from app.schemas.models import IncidentBundle, ScenarioType
from app.services.scenario_classifier import ScenarioClassifier


def _load_bundle(path: Path) -> IncidentBundle:
    return IncidentBundle.model_validate(json.loads(path.read_text(encoding="utf-8")))


def test_classifies_certificate_issue(sample_dir: Path) -> None:
    bundle = _load_bundle(sample_dir / "cert_expiry_auth_service.json")
    classifier = ScenarioClassifier()
    assert classifier.classify(bundle) == ScenarioType.CERTIFICATE_ISSUE


def test_classifies_retry_storm(sample_dir: Path) -> None:
    bundle = _load_bundle(sample_dir / "retry_storm_payments.json")
    classifier = ScenarioClassifier()
    assert classifier.classify(bundle) == ScenarioType.RETRY_STORM


def test_classifies_dependency_outage(sample_dir: Path) -> None:
    bundle = _load_bundle(sample_dir / "dependency_outage_notifications.json")
    classifier = ScenarioClassifier()
    assert classifier.classify(bundle) == ScenarioType.DEPENDENCY_OUTAGE
