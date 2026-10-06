from __future__ import annotations
import mimetypes
from pathlib import Path
from urllib.parse import quote
import httpx
from .config import settings

def _headers():
    return {
        "Authorization": f"Bearer {settings.github_token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

async def _get_or_create_release():
    if not settings.github_token or not settings.github_repo:
        raise RuntimeError("GITHUB_TOKEN and GITHUB_REPO are required for MEDIA_STORE=github")
    base = "https://api.github.com"
    async with httpx.AsyncClient(timeout=120) as client:
        r = await client.get(
            f"{base}/repos/{settings.github_repo}/releases/tags/{quote(settings.github_release_tag)}",
            headers=_headers(),
        )
        if r.status_code == 200:
            return r.json()

        r = await client.post(
            f"{base}/repos/{settings.github_repo}/releases",
            headers={**_headers(), "Content-Type": "application/json"},
            json={
                "tag_name": settings.github_release_tag,
                "name": "ARTCLASS generated media",
                "body": "Generated media assets for ARTCLASS.",
                "draft": False,
                "prerelease": False,
            },
        )
        r.raise_for_status()
        return r.json()

async def publish_public_media(path: str) -> str:
    if settings.media_store == "local":
        return f"{settings.public_base_url}/media/{quote(Path(path).name)}"

    release = await _get_or_create_release()
    name = Path(path).name
    mime = mimetypes.guess_type(name)[0] or "application/octet-stream"
    upload_url = release["upload_url"].split("{")[0] + f"?name={quote(name)}"

    async with httpx.AsyncClient(timeout=300) as client:
        with open(path, "rb") as f:
            payload = f.read()
        r = await client.post(
            upload_url,
            headers={**_headers(), "Content-Type": mime},
            content=payload,
        )
        r.raise_for_status()
        return r.json()["browser_download_url"]
