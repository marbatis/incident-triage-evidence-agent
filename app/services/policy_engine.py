from __future__ import annotations

from dataclasses import dataclass

from app.schemas.models import IncidentBundle, RetrievedEvidence, ScenarioType, Severity


@dataclass
class PolicyDecision:
    severity: Severity
    escalation_target: str
    likely_root_causes: list[str]
    safe_next_actions: list[str]
    missing_context: list[str]
    score: float


class PolicyEngine:
    def evaluate(
        self,
        bundle: IncidentBundle,
        scenario_type: ScenarioType,
        likely_service: str,
        evidence: list[RetrievedEvidence],
    ) -> PolicyDecision:
        missing = self._detect_missing_context(bundle, evidence)
        score = self._score(bundle, scenario_type, missing)
        severity = self._severity_from_score(score)
        escalation = self._escalation_target(severity)

        return PolicyDecision(
            severity=severity,
            escalation_target=escalation,
            likely_root_causes=self._root_causes(scenario_type, bundle),
            safe_next_actions=self._safe_actions(scenario_type, likely_service),
            missing_context=missing,
            score=score,
        )

    def _score(
        self,
        bundle: IncidentBundle,
        scenario_type: ScenarioType,
        missing_context: list[str],
    ) -> float:
        base_map = {
            ScenarioType.CERTIFICATE_ISSUE: 58.0,
            ScenarioType.RETRY_STORM: 42.0,
            ScenarioType.DEPENDENCY_OUTAGE: 55.0,
            ScenarioType.UNKNOWN: 35.0,
        }
        score = base_map.get(scenario_type, 45.0)

        if bundle.environment.lower() in {"prod", "production"}:
            score += 8

        metric_map = {
            metric.metric_name.lower(): metric.value for metric in bundle.metric_snapshots
        }

        cert_days = metric_map.get("cert_expiry_days")
        if cert_days is not None:
            if cert_days <= 1:
                score += 28
            elif cert_days <= 3:
                score += 20
            elif cert_days <= 7:
                score += 10

        retry_rate = metric_map.get("retry_rate_per_min")
        if retry_rate is not None:
            if retry_rate >= 1000:
                score += 16
            elif retry_rate >= 300:
                score += 10

        p99_latency = metric_map.get("p99_latency_ms")
        if p99_latency is not None:
            if p99_latency >= 3000:
                score += 8
            elif p99_latency >= 1500:
                score += 4

        dep_error_rate = metric_map.get("dependency_error_rate")
        if dep_error_rate is not None:
            if dep_error_rate >= 0.2:
                score += 18
            elif dep_error_rate >= 0.1:
                score += 10

        for alert in bundle.alerts:
            sev = alert.severity.lower()
            if sev in {"critical", "sev1", "p1"}:
                score += 10
            elif sev in {"high", "sev2", "p2"}:
                score += 4

        for log in bundle.logs:
            lowered = log.message.lower()
            if any(token in lowered for token in {"expired", "handshake failure", "x509"}):
                score += 6
            if any(
                token in lowered
                for token in {"timeout", "429", "connection refused", "unavailable"}
            ):
                score += 4

        if len(bundle.affected_services) >= 3:
            score += 8

        if len(missing_context) >= 2:
            score += 8

        return max(0.0, min(score, 100.0))

    def _severity_from_score(self, score: float) -> Severity:
        if score >= 92:
            return Severity.SEV1
        if score >= 60:
            return Severity.SEV2
        return Severity.SEV3

    def _escalation_target(self, severity: Severity) -> str:
        if severity == Severity.SEV1:
            return "incident_commander_oncall"
        if severity == Severity.SEV2:
            return "service_owner_oncall"
        return "team_triage_queue"

    def _root_causes(self, scenario_type: ScenarioType, bundle: IncidentBundle) -> list[str]:
        if scenario_type == ScenarioType.CERTIFICATE_ISSUE:
            return [
                "Certificate nearing expiry or already expired",
                "Handshake failures causing authentication disruptions",
            ]
        if scenario_type == ScenarioType.RETRY_STORM:
            return [
                "Aggressive retry behavior amplifying load",
                "Timeouts and throttling creating self-reinforcing failure",
            ]
        if scenario_type == ScenarioType.DEPENDENCY_OUTAGE:
            return [
                "Downstream dependency unavailable or saturated",
                "Error propagation from dependency into upstream services",
            ]
        return [f"Insufficient deterministic signal in incident {bundle.incident_id}"]

    def _safe_actions(self, scenario_type: ScenarioType, likely_service: str) -> list[str]:
        common = [
            f"Declare triage lead for {likely_service}",
            "Capture a timestamped incident timeline",
            "Confirm current customer impact and blast radius",
        ]

        if scenario_type == ScenarioType.CERTIFICATE_ISSUE:
            return common + [
                "Verify cert expiry and trust chain on active endpoints",
                "Prepare controlled certificate rotation with rollback plan",
                "Pause non-essential deploys touching auth path",
            ]
        if scenario_type == ScenarioType.RETRY_STORM:
            return common + [
                "Temporarily reduce retry concurrency and backoff aggressiveness",
                "Rate-limit noisy callers where safe",
                "Validate queue depth and recover consumers gradually",
            ]
        if scenario_type == ScenarioType.DEPENDENCY_OUTAGE:
            return common + [
                "Switch to degraded mode or cached fallback if available",
                "Coordinate with dependency owner and share error evidence",
                "Throttle non-critical traffic until dependency stabilizes",
            ]
        return common + ["Collect additional alerts, logs, and runbook context before escalation"]

    def _detect_missing_context(
        self,
        bundle: IncidentBundle,
        evidence: list[RetrievedEvidence],
    ) -> list[str]:
        missing: list[str] = []

        if not bundle.alerts:
            missing.append("No alerts were provided")
        if not bundle.logs:
            missing.append("No logs were provided")
        if not bundle.metric_snapshots:
            missing.append("No metric snapshots were provided")
        if not bundle.affected_services:
            missing.append("Affected services were not specified")
        if not bundle.runbook_refs:
            missing.append("Runbook references were not provided")

        has_runbook_evidence = any(item.source_type == "runbook" for item in evidence)
        if not has_runbook_evidence:
            missing.append("No runbook evidence matched this incident")

        return missing
