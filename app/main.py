from __future__ import annotations

import json
from pathlib import Path

from fastapi import BackgroundTasks, Depends, FastAPI, Header, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .config import settings
from .db import add_schedule, get_job, init_db, new_job
from .pipeline import build_job
from .worker import run_once

app = FastAPI(
    title="ARTCLASS AI Content Agent",
    version="1.1.0",
    description="Single-message content generation, rendering, scheduling and Instagram publishing.",
)

Path(settings.media_dir).mkdir(parents=True, exist_ok=True)
Path("data").mkdir(exist_ok=True)
app.mount("/media", StaticFiles(directory=settings.media_dir), name="media")

class ContentRequest(BaseModel):
    message: str = Field(min_length=3, max_length=4000)
    style: str = Field(default="professional minimal", max_length=200)
    duration: int = Field(default=15, ge=6, le=60)
    schedule_at: str | None = None
    daily: bool | None = None
    timezone: str | None = None
    auto_schedule: bool = True

class CreateRequest(ContentRequest):
    prompt: str | None = None

class ScheduleRequest(BaseModel):
    job_id: str
    scheduled_at: str
    daily: bool = False
    timezone: str = "UTC"

class WorkerRequest(BaseModel):
    worker_key: str

def auth(x_api_key: str | None = Header(default=None)) -> None:
    if settings.api_key and x_api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")

@app.on_event("startup")
async def startup():
    init_db()

@app.get("/health")
def health():
    return {"ok": True, "service": "artclass-ai-content", "version": app.version}

@app.get("/")
def root():
    return {
        "service": "ARTCLASS AI Content Agent",
        "docs": "/docs",
        "mode": "open-source/local-first",
        "single_message": True,
    }

@app.post("/v1/content", dependencies=[Depends(auth)])
async def content(req: ContentRequest, background: BackgroundTasks):
    job_id = new_job(req.message)
    background.add_task(
        finish_job,
        job_id,
        req.message,
        req.style,
        req.duration,
        req.schedule_at,
        req.daily,
        req.timezone,
        req.auto_schedule,
    )
    return {"job_id": job_id, "status": "processing"}

@app.post("/v1/create", dependencies=[Depends(auth)])
async def create(req: CreateRequest, background: BackgroundTasks):
    message = req.message or req.prompt or ""
    if not message:
        raise HTTPException(status_code=422, detail="message is required")
    job_id = new_job(message)
    background.add_task(
        finish_job,
        job_id,
        message,
        req.style,
        req.duration,
        req.schedule_at,
        req.daily,
        req.timezone,
        req.auto_schedule,
    )
    return {"job_id": job_id, "status": "processing"}

async def finish_job(
    job_id: str,
    message: str,
    style: str,
    duration: int,
    schedule_at: str | None,
    daily: bool | None,
    timezone_name: str | None,
    auto_schedule: bool,
):
    await build_job(
        job_id,
        message,
        style,
        duration,
        schedule_at,
        daily,
        timezone_name or settings.default_timezone,
        auto_schedule,
    )

@app.get("/v1/jobs/{job_id}", dependencies=[Depends(auth)])
def job(job_id: str):
    item = get_job(job_id)
    if not item:
        raise HTTPException(status_code=404, detail="Job not found")
    return item

@app.post("/v1/schedule", dependencies=[Depends(auth)])
def schedule(req: ScheduleRequest):
    item = get_job(req.job_id)
    if not item:
        raise HTTPException(status_code=404, detail="Job not found")
    if not item.get("media_urls"):
        raise HTTPException(status_code=400, detail="This content has no publishable media")
    return {
        "schedule_id": add_schedule(req.job_id, req.scheduled_at, req.daily, req.timezone),
        "status": "scheduled",
    }

@app.post("/v1/worker/run", dependencies=[Depends(auth)])
async def worker(req: WorkerRequest):
    if settings.worker_key and req.worker_key != settings.worker_key:
        raise HTTPException(status_code=401, detail="Invalid worker key")
    return {"results": await run_once()}
