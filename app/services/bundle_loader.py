from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from pydantic import ValidationError

from app.schemas.models import IncidentBundle


class BundleLoader:
    def __init__(self, data_dir: Optional[Path] = None):
        root = Path(__file__).resolve().parents[2]
        self.sample_dir = (data_dir or root / "data") / "sample_bundles"

    def list_sample_ids(self) -> list[str]:
        return sorted(path.stem for path in self.sample_dir.glob("*.json"))

    def load_sample(self, sample_id: str) -> IncidentBundle:
        allowed = self.list_sample_ids()
        if sample_id not in allowed:
            raise FileNotFoundError(f"Unknown sample_id: {sample_id}")
        path = self.sample_dir / f"{sample_id}.json"
        return self._parse_file(path)

    def parse_bundle_payload(self, payload: dict[str, Any]) -> IncidentBundle:
        try:
            return IncidentBundle.model_validate(payload)
        except ValidationError:
            raise

    def parse_upload_bytes(self, raw_bytes: bytes) -> IncidentBundle:
        payload = json.loads(raw_bytes.decode("utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("Uploaded payload must be a JSON object")
        return self.parse_bundle_payload(payload)

    def _parse_file(self, path: Path) -> IncidentBundle:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return self.parse_bundle_payload(payload)
