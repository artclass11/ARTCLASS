from __future__ import annotations
import json
from .content import generate
from .db import new_job, update_job
from .media_store import publish_public_media
from .video import render_card_reel

async def create_reel_job(prompt: str, style: str, duration: int) -> str:
    job_id = new_job(prompt)
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
            video_url=url,
        )
    except Exception as exc:
        update_job(job_id, status="error", error=str(exc))
    return job_id
