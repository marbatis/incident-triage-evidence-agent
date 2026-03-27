from __future__ import annotations

from app.schemas.models import IncidentBundle, ScenarioType


class ScenarioClassifier:
    CERT_KEYWORDS = {"cert", "certificate", "x509", "tls", "ssl", "expiry", "expired"}
    RETRY_KEYWORDS = {"retry", "timeout", "429", "throttle", "backoff", "retry storm"}
    DEPENDENCY_KEYWORDS = {
        "dependency",
        "downstream",
        "unavailable",
        "dns",
        "connection refused",
        "upstream",
        "saturation",
    }

    def classify(self, bundle: IncidentBundle) -> ScenarioType:
        text = self._bundle_text(bundle)

        cert_hits = self._count_keyword_hits(text, self.CERT_KEYWORDS)
        retry_hits = self._count_keyword_hits(text, self.RETRY_KEYWORDS)
        dep_hits = self._count_keyword_hits(text, self.DEPENDENCY_KEYWORDS)

        # Metric hints have higher signal than plain text.
        metric_map = {m.metric_name.lower(): m.value for m in bundle.metric_snapshots}
        if metric_map.get("cert_expiry_days", 999) <= 7:
            cert_hits += 3
        if metric_map.get("retry_rate_per_min", 0) >= 300:
            retry_hits += 3
        if metric_map.get("dependency_error_rate", 0) >= 0.1:
            dep_hits += 3

        scored = [
            (ScenarioType.CERTIFICATE_ISSUE, cert_hits),
            (ScenarioType.RETRY_STORM, retry_hits),
            (ScenarioType.DEPENDENCY_OUTAGE, dep_hits),
        ]
        scored.sort(key=lambda item: item[1], reverse=True)

        best_type, best_score = scored[0]
        if best_score <= 0:
            return ScenarioType.UNKNOWN
        return best_type

    def detect_likely_service(self, bundle: IncidentBundle) -> str:
        if bundle.affected_services:
            return bundle.affected_services[0]

        text = self._bundle_text(bundle)
        for item in bundle.service_topology:
            if item.service.lower() in text:
                return item.service

        if bundle.service_topology:
            return bundle.service_topology[0].service

        return "unknown_service"

    def _bundle_text(self, bundle: IncidentBundle) -> str:
        parts: list[str] = [bundle.title.lower()]
        parts.extend(alert.message.lower() for alert in bundle.alerts)
        parts.extend(log.message.lower() for log in bundle.logs)
        parts.extend(change.summary.lower() for change in bundle.recent_changes)
        parts.extend(ref.lower() for ref in bundle.runbook_refs)
        parts.extend(service.lower() for service in bundle.affected_services)
        parts.extend(m.metric_name.lower() for m in bundle.metric_snapshots)
        return " ".join(parts)

    @staticmethod
    def _count_keyword_hits(text: str, keywords: set[str]) -> int:
        return sum(1 for keyword in keywords if keyword in text)
