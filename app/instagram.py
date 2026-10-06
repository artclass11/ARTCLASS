from __future__ import annotations
import asyncio
import httpx
from .config import settings

def _base():
    return f"{settings.meta_graph_base}/{settings.meta_graph_version}"

def _ready():
    if not settings.instagram_user_id or not settings.instagram_access_token:
        raise RuntimeError("Instagram credentials are not configured")

async def publish_reel(video_url: str, caption: str) -> str:
    _ready()
    async with httpx.AsyncClient(timeout=120) as client:
        r = await client.post(
            f"{_base()}/{settings.instagram_user_id}/media",
            data={
                "media_type": "REELS",
                "video_url": video_url,
                "caption": caption,
                "share_to_feed": "true",
                "access_token": settings.instagram_access_token,
            },
        )
        r.raise_for_status()
        creation_id = r.json()["id"]

        for _ in range(40):
            s = await client.get(
                f"{_base()}/{creation_id}",
                params={
                    "fields": "status_code",
                    "access_token": settings.instagram_access_token,
                },
            )
            s.raise_for_status()
            code = s.json().get("status_code", "")
            if code == "FINISHED":
                break
            if code in {"ERROR", "EXPIRED"}:
                raise RuntimeError(f"Instagram container status: {code}")
            await asyncio.sleep(3)

        p = await client.post(
            f"{_base()}/{settings.instagram_user_id}/media_publish",
            data={
                "creation_id": creation_id,
                "access_token": settings.instagram_access_token,
            },
        )
        p.raise_for_status()
        return p.json()["id"]
