from __future__ import annotations

import json

from .content import generate
from .db import add_schedule, claim_job, update_job
from .media_store import publish_public_media_many
from .video import render_content

async def build_job(
    job_id: str,
    message: str,
    style: str,
    duration: int,
    schedule_at: str | None,
    daily: bool | None,
    timezone_name: str | None,
    auto_schedule: bool,
) -> bool:
    if not claim_job(job_id):
        return False

    try:
        package = await generate(
            message,
            style=style,
            duration=duration,
            timezone_name=timezone_name,
        )
        media_type, paths = render_content(package)
        media_urls = await publish_public_media_many(paths) if paths else []

        caption = str(package.get("caption", "")).strip()
        hashtags = package.get("hashtags", [])
        if hashtags:
            caption = f"{caption}\n\n{' '.join(hashtags)}"

        update_job(
            job_id,
            status="ready",
            title=package.get("title", ""),
            caption=caption,
            hashtags=json.dumps(hashtags),
            script_json=json.dumps(package),
            video_path=paths[0] if paths else None,
            video_url=media_urls[0] if media_urls else None,
            media_type=media_type,
            media_urls=json.dumps(media_urls),
            content_type=package.get("content_type", "reel"),
            platform=package.get("platform", "instagram"),
        )

        desired_schedule = schedule_at or package.get("scheduled_at")
        desired_daily = daily if daily is not None else bool(package.get("daily", False))
        platform = package.get("platform", "instagram")
        if auto_schedule and desired_schedule and platform == "instagram" and media_type in {"video", "image", "carousel"}:
            add_schedule(
                job_id,
                desired_schedule,
                desired_daily,
                timezone_name or package.get("timezone") or "UTC",
            )
        return True
    except Exception as exc:
        update_job(job_id, status="error", error=str(exc))
        return False
