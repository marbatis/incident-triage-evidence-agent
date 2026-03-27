from __future__ import annotations

import json

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db import get_db
from app.schemas.models import TriageResult
from app.services.triage_service import TriageService

router = APIRouter(prefix="/api", tags=["api"])


def get_triage_service(db: Session = Depends(get_db)) -> TriageService:
    return TriageService(db)


def get_app_settings() -> Settings:
    return get_settings()


@router.post(
    "/triage/sample/{sample_id}",
    response_model=TriageResult,
    status_code=status.HTTP_201_CREATED,
)
def triage_sample(
    sample_id: str,
    service: TriageService = Depends(get_triage_service),
) -> TriageResult:
    try:
        return service.assess_sample(sample_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post(
    "/triage/upload",
    response_model=TriageResult,
    status_code=status.HTTP_201_CREATED,
)
async def triage_upload(
    file: UploadFile = File(...),
    service: TriageService = Depends(get_triage_service),
    settings: Settings = Depends(get_app_settings),
) -> TriageResult:
    raw = await file.read(settings.max_upload_bytes + 1)
    if len(raw) > settings.max_upload_bytes:
        raise HTTPException(status_code=413, detail="Uploaded file exceeds size limit")

    try:
        payload = json.loads(raw.decode("utf-8"))
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Uploaded file is not valid JSON") from exc

    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Uploaded JSON must be an object")

    try:
        return service.assess_payload(payload)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/triage/{triage_id}", response_model=TriageResult)
def get_triage(
    triage_id: str,
    service: TriageService = Depends(get_triage_service),
) -> TriageResult:
    result = service.get_triage(triage_id)
    if not result:
        raise HTTPException(status_code=404, detail="Triage result not found")
    return result
