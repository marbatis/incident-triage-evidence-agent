from __future__ import annotations

from abc import ABC, abstractmethod

from app.schemas.models import TriageResult


class MemoProvider(ABC):
    @abstractmethod
    def generate_memo(self, result: TriageResult) -> str:
        """Generate a concise incident memo from deterministic triage output."""
