from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db import get_db
from app.services.triage_service import TriageService

router = APIRouter(tags=["web"])
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parents[1] / "templates"))


def get_triage_service(db: Session = Depends(get_db)) -> TriageService:
    return TriageService(db)


@router.get("/", response_class=HTMLResponse)
def home(request: Request, service: TriageService = Depends(get_triage_service)) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"samples": service.list_samples()},
    )


@router.post("/triage/sample/{sample_id}")
def run_sample(
    sample_id: str,
    service: TriageService = Depends(get_triage_service),
) -> RedirectResponse:
    result = service.assess_sample(sample_id)
    return RedirectResponse(url=f"/triage/{result.triage_id}", status_code=303)


@router.post("/triage/upload")
async def run_upload(
    file: UploadFile = File(...),
    service: TriageService = Depends(get_triage_service),
    settings: Settings = Depends(get_settings),
) -> RedirectResponse:
    raw = await file.read(settings.max_upload_bytes + 1)
    if len(raw) > settings.max_upload_bytes:
        raise HTTPException(status_code=413, detail="Uploaded file exceeds size limit")

    try:
        payload = json.loads(raw.decode("utf-8"))
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Uploaded file is not valid JSON") from exc

    result = service.assess_payload(payload)
    return RedirectResponse(url=f"/triage/{result.triage_id}", status_code=303)


@router.get("/triage/{triage_id}", response_class=HTMLResponse)
def triage_detail(
    triage_id: str,
    request: Request,
    service: TriageService = Depends(get_triage_service),
) -> HTMLResponse:
    result = service.get_triage(triage_id)
    if not result:
        raise HTTPException(status_code=404, detail="Triage result not found")

    return templates.TemplateResponse(
        request=request,
        name="triage_detail.html",
        context={"result": result},
    )


@router.get("/history", response_class=HTMLResponse)
def history(
    request: Request,
    service: TriageService = Depends(get_triage_service),
    limit: int = Query(default=100, ge=1, le=500),
) -> HTMLResponse:
    rows = service.history(limit=limit)
    return templates.TemplateResponse(
        request=request,
        name="history.html",
        context={"rows": rows},
    )
