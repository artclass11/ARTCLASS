from __future__ import annotations
from pathlib import Path
from fastapi import BackgroundTasks, Depends, FastAPI, Header, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from .config import settings
from .content import generate
from .db import add_schedule, get_job, init_db, new_job, update_job
from .instagram import publish_reel
from .media_store import publish_public_media
from .video import render_card_reel
from .worker import run_once
import json

app = FastAPI(
    title="ARTCLASS AI Instagram Agent",
    version="1.0.0",
    description="Prompt to Reel to schedule to official Instagram publishing."
)

Path(settings.media_dir).mkdir(parents=True, exist_ok=True)
Path("data").mkdir(exist_ok=True)
app.mount("/media", StaticFiles(directory=settings.media_dir), name="media")

class CreateRequest(BaseModel):
    prompt: str = Field(min_length=3, max_length=4000)
    style: str = Field(default="premium minimal", max_length=200)
    duration: int = Field(default=15, ge=6, le=60)
    schedule_at: str | None = None
    daily: bool = False
    timezone: str = "UTC"

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
    return {"ok": True, "service": "artclass-ai-instagram", "version": app.version}

@app.get("/")
def root():
    return {"service": "ARTCLASS AI Instagram Agent", "docs": "/docs", "mode": "open-source/local-first"}

@app.post("/v1/create", dependencies=[Depends(auth)])
async def create(req: CreateRequest, background: BackgroundTasks):
    job_id = new_job(req.prompt)
    background.add_task(
        finish_job, job_id, req.prompt, req.style, req.duration,
        req.schedule_at, req.daily, req.timezone
    )
    return {"job_id": job_id, "status": "processing"}

async def finish_job(job_id, prompt, style, duration, schedule_at, daily, timezone_name):
    try:
        package = await generate(prompt, style=style, duration=duration)
        path = render_card_reel(package)
        url = await publish_public_media(path)
        hashtags = package.get("hashtags", [])
        caption = str(package.get("caption", "")).strip()
        if hashtags:
            caption = f"{caption}\n\n{' '.join(hashtags)}"
        update_job(
            job_id,
            status="ready",
            title=package.get("title", ""),
            caption=caption,
            hashtags=json.dumps(hashtags),
            script_json=json.dumps(package),
            video_path=path,
            video_url=url
        )
        if schedule_at:
            add_schedule(job_id, schedule_at, daily, timezone_name)
    except Exception as exc:
        update_job(job_id, status="error", error=str(exc))

@app.get("/v1/jobs/{job_id}", dependencies=[Depends(auth)])
def job(job_id: str):
    item = get_job(job_id)
    if not item:
        raise HTTPException(status_code=404, detail="Job not found")
    return item

@app.post("/v1/schedule", dependencies=[Depends(auth)])
def schedule(req: ScheduleRequest):
    if not get_job(req.job_id):
        raise HTTPException(status_code=404, detail="Job not found")
    return {
        "schedule_id": add_schedule(req.job_id, req.scheduled_at, req.daily, req.timezone),
        "status": "scheduled"
    }

@app.post("/v1/worker/run", dependencies=[Depends(auth)])
async def worker(req: WorkerRequest):
    if settings.worker_key and req.worker_key != settings.worker_key:
        raise HTTPException(status_code=401, detail="Invalid worker key")
    return {"results": await run_once()}
