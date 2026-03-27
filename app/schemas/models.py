from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class ScenarioType(str, Enum):
    CERTIFICATE_ISSUE = "certificate_issue"
    RETRY_STORM = "retry_storm"
    DEPENDENCY_OUTAGE = "dependency_outage"
    UNKNOWN = "unknown"


class Severity(str, Enum):
    SEV1 = "SEV1"
    SEV2 = "SEV2"
    SEV3 = "SEV3"


class Alert(BaseModel):
    name: str
    severity: str = "warning"
    message: str
    source: Optional[str] = None


class MetricSnapshot(BaseModel):
    metric_name: str
    value: float
    unit: Optional[str] = None
    window: Optional[str] = None


class ServiceTopologyItem(BaseModel):
    service: str
    depends_on: list[str] = Field(default_factory=list)


class RecentChange(BaseModel):
    change_id: str
    summary: str
    timestamp: Optional[datetime] = None


class LogEntry(BaseModel):
    timestamp: Optional[datetime] = None
    level: str = "INFO"
    message: str


class IncidentBundle(BaseModel):
    incident_id: str
    title: str
    timestamp: datetime
    alerts: list[Alert] = Field(default_factory=list)
    metric_snapshots: list[MetricSnapshot] = Field(default_factory=list)
    service_topology: list[ServiceTopologyItem] = Field(default_factory=list)
    recent_changes: list[RecentChange] = Field(default_factory=list)
    runbook_refs: list[str] = Field(default_factory=list)
    logs: list[LogEntry] = Field(default_factory=list)
    affected_services: list[str] = Field(default_factory=list)
    environment: str
    severity_hint: Optional[str] = None

    @field_validator("incident_id")
    @classmethod
    def validate_incident_id(cls, value: str) -> str:
        if not value or len(value.strip()) < 3:
            raise ValueError("incident_id must be at least 3 characters")
        return value.strip()


class RetrievedEvidence(BaseModel):
    source_type: str
    source_name: str
    excerpt: str
    relevance_score: float = Field(ge=0.0, le=1.0)
    citation_id: str


class TriageResult(BaseModel):
    triage_id: str
    incident_id: str
    scenario_type: ScenarioType
    likely_service: str
    likely_root_causes: list[str]
    severity: Severity
    escalation_target: str
    safe_next_actions: list[str]
    evidence: list[RetrievedEvidence]
    missing_context: list[str]
    memo: str
    score: float = Field(ge=0.0, le=100.0)
    created_at: datetime


class TriageHistoryItem(BaseModel):
    triage_id: str
    incident_id: str
    scenario_type: ScenarioType
    likely_service: str
    severity: Severity
    escalation_target: str
    score: float
    created_at: datetime
