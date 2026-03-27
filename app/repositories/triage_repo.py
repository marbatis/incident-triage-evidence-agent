from __future__ import annotations

import json
from typing import Any, Optional

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models import TriageRecord


class TriageRepository:
    def __init__(self, db: Session):
        self.db = db

    def save(self, bundle: dict[str, Any], result: dict[str, Any]) -> None:
        record = TriageRecord(
            triage_id=result["triage_id"],
            incident_id=result["incident_id"],
            scenario_type=result["scenario_type"],
            likely_service=result["likely_service"],
            severity=result["severity"],
            escalation_target=result["escalation_target"],
            score=float(result["score"]),
            bundle_json=json.dumps(bundle, default=str),
            result_json=json.dumps(result, default=str),
        )
        self.db.add(record)
        self.db.commit()

    def get_result(self, triage_id: str) -> Optional[dict[str, Any]]:
        stmt = select(TriageRecord).where(TriageRecord.triage_id == triage_id)
        record = self.db.scalar(stmt)
        if not record:
            return None
        return json.loads(record.result_json)

    def list_recent(self, limit: int = 100) -> list[dict[str, Any]]:
        stmt = select(TriageRecord).order_by(desc(TriageRecord.created_at)).limit(limit)
        rows = self.db.scalars(stmt).all()
        return [json.loads(row.result_json) for row in rows]
