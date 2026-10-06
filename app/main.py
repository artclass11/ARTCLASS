from __future__ import annotations

from typing import Optional

from fastapi import FastAPI
from pydantic import BaseModel, Field

from app.config import ensure_output_dir
from app.services.instagram import schedule_instagram_post
from app.services.llm import generate_storyboard
from app.services.video import create_reel_video

app = FastAPI(title="ARTCLASS AI Content Agent", version="0.1.0")


class GenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=10)
    style: str = "cinematic"
    duration_seconds: int = 15
    aspect_ratio: str = "9:16"


class ScheduleRequest(BaseModel):
    file_path: str
    caption: str
    scheduled_at: Optional[str] = None
    account_id: Optional[str] = None


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "ARTCLASS"}


@app.post("/generate")
def generate_video(payload: GenerateRequest) -> dict:
    ensure_output_dir()
    storyboard = generate_storyboard(payload.prompt, style=payload.style)
    video_path = create_reel_video(
        prompt=payload.prompt,
        storyboard=storyboard,
        duration_seconds=payload.duration_seconds,
        aspect_ratio=payload.aspect_ratio,
    )
    return {
        "status": "created",
        "storyboard": storyboard,
        "video_path": video_path,
    }


@app.post("/schedule")
def schedule(payload: ScheduleRequest) -> dict:
    result = schedule_instagram_post(
        file_path=payload.file_path,
        caption=payload.caption,
        scheduled_at=payload.scheduled_at,
        account_id=payload.account_id,
    )
    return result
