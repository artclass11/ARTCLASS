from __future__ import annotations

import asyncio
import httpx

from .config import settings

def _base():
    return f"{settings.meta_graph_base}/{settings.meta_graph_version}"

def _ready():
    if not settings.instagram_user_id or not settings.instagram_access_token:
        raise RuntimeError("Instagram credentials are not configured")

async def _wait_container(client: httpx.AsyncClient, container_id: str) -> None:
    for _ in range(40):
        r = await client.get(
            f"{_base()}/{container_id}",
            params={"fields": "status_code", "access_token": settings.instagram_access_token},
        )
        r.raise_for_status()
        code = r.json().get("status_code", "")
        if code == "FINISHED":
            return
        if code in {"ERROR", "EXPIRED"}:
            raise RuntimeError(f"Instagram container status: {code}")
        await asyncio.sleep(3)
    raise TimeoutError("Instagram media container did not finish in time")

async def _publish_container(client: httpx.AsyncClient, creation_id: str) -> str:
    r = await client.post(
        f"{_base()}/{settings.instagram_user_id}/media_publish",
        data={"creation_id": creation_id, "access_token": settings.instagram_access_token},
    )
    r.raise_for_status()
    return r.json()["id"]

async def publish_media(media_type: str, media_urls: list[str], caption: str) -> str:
    _ready()
    if not media_urls:
        raise ValueError("No media URLs supplied")

    async with httpx.AsyncClient(timeout=120) as client:
        if media_type == "carousel":
            child_ids = []
            for url in media_urls[:10]:
                r = await client.post(
                    f"{_base()}/{settings.instagram_user_id}/media",
                    data={
                        "image_url": url,
                        "is_carousel_item": "true",
                        "access_token": settings.instagram_access_token,
                    },
                )
                r.raise_for_status()
                child_ids.append(r.json()["id"])
            r = await client.post(
                f"{_base()}/{settings.instagram_user_id}/media",
                data={
                    "media_type": "CAROUSEL",
                    "children": ",".join(child_ids),
                    "caption": caption,
                    "access_token": settings.instagram_access_token,
                },
            )
            r.raise_for_status()
            return await _publish_container(client, r.json()["id"])

        if media_type == "image":
            payload = {
                "image_url": media_urls[0],
                "caption": caption,
                "access_token": settings.instagram_access_token,
            }
        elif media_type == "story_image":
            payload = {
                "image_url": media_urls[0],
                "media_type": "STORIES",
                "access_token": settings.instagram_access_token,
            }
        elif media_type == "story_video":
            payload = {
                "video_url": media_urls[0],
                "media_type": "STORIES",
                "access_token": settings.instagram_access_token,
            }
        else:
            payload = {
                "media_type": "REELS",
                "video_url": media_urls[0],
                "caption": caption,
                "share_to_feed": "true",
                "access_token": settings.instagram_access_token,
            }

        r = await client.post(
            f"{_base()}/{settings.instagram_user_id}/media",
            data=payload,
        )
        r.raise_for_status()
        creation_id = r.json()["id"]
        await _wait_container(client, creation_id)
        return await _publish_container(client, creation_id)

async def publish_reel(video_url: str, caption: str) -> str:
    return await publish_media("video", [video_url], caption)
