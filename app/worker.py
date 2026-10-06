from __future__ import annotations

from datetime import datetime, timedelta

from .db import add_schedule, due_schedules, mark_schedule
from .instagram import publish_media

async def run_once(limit: int = 10) -> list[dict]:
    results = []
    for item in due_schedules(limit):
        try:
            media_type = item.get("media_type") or "video"
            media_urls = item.get("media_urls")
            if isinstance(media_urls, str):
                import json
                media_urls = json.loads(media_urls)
            media_urls = media_urls or ([item["video_url"]] if item.get("video_url") else [])
            if media_type == "text" or not media_urls:
                raise ValueError("Scheduled job has no publishable media")

            media_id = await publish_media(media_type, media_urls, item["caption"] or "")
            mark_schedule(item["id"], "published", published_media_id=media_id)
            results.append({
                "schedule_id": item["id"],
                "status": "published",
                "media_id": media_id,
            })

            if item["daily"]:
                next_dt = datetime.fromisoformat(item["scheduled_at"]) + timedelta(days=1)
                add_schedule(
                    item["job_id"],
                    next_dt.isoformat(),
                    True,
                    item["timezone"],
                )
        except Exception as exc:
            mark_schedule(item["id"], "error", last_error=str(exc))
            results.append({
                "schedule_id": item["id"],
                "status": "error",
                "error": str(exc),
            })
    return results
