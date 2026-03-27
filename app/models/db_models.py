from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class TriageRecord(Base):
    __tablename__ = "triage_history"

    triage_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    incident_id: Mapped[str] = mapped_column(String(128), index=True)
    scenario_type: Mapped[str] = mapped_column(String(64), index=True)
    likely_service: Mapped[str] = mapped_column(String(128), index=True)
    severity: Mapped[str] = mapped_column(String(32), index=True)
    escalation_target: Mapped[str] = mapped_column(String(128))
    score: Mapped[float] = mapped_column(Float)
    bundle_json: Mapped[str] = mapped_column(Text)
    result_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
