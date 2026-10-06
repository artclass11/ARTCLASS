from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

import httpx
from dateparser import parse as parse_date

from .config import settings

ALLOWED_TYPES = {
    "reel", "story", "post", "carousel", "caption", "script", "blog", "ad",
    "email", "newsletter", "product_description", "landing_page", "youtube_script",
}
ALLOWED_PLATFORMS = {"instagram", "facebook", "youtube", "tiktok", "linkedin", "x", "generic"}

SYSTEM = """You are ARTCLASS, a professional multi-format content director.
Turn one natural-language brief into a production-ready content plan.
Return ONLY valid JSON with these keys:
title, platform, content_type, duration_seconds, hook, scenes, slides, voiceover,
caption, hashtags, cta, schedule_text, daily, timezone.
platform must be one of: instagram, facebook, youtube, tiktok, linkedin, x, generic.
content_type must be one of: reel, story, post, carousel, caption, script, blog, ad, email, newsletter, product_description, landing_page, youtube_script.
For reel/story scenes, return 4-8 objects with text and visual.
For carousel slides, return 3-10 objects with title and body.
For text-only content, scenes/slides can be empty.
schedule_text should preserve the requested natural-language time phrase or be empty.
daily is true only when the user clearly asks for recurring daily posting.
timezone should be a valid IANA timezone when explicitly or implicitly clear.
Style: professional, concise, original, useful. Avoid unsupported factual claims and copyrighted imitation."""

FALLBACK = {
    "title": "Daily idea",
    "platform": "instagram",
    "content_type": "reel",
    "duration_seconds": 15,
    "hook": "Here is one useful idea worth trying today.",
    "scenes": [
        {"text": "Start with one clear goal.", "visual": "minimal editorial title card"},
        {"text": "Show the useful detail quickly.", "visual": "clean motion card"},
        {"text": "Give one practical takeaway.", "visual": "bold takeaway card"},
        {"text": "Make the next step easy.", "visual": "simple call to action card"},
    ],
    "slides": [],
    "voiceover": "",
    "caption": "A simple idea, made useful. Save this for later.",
    "hashtags": ["#contentcreator", "#reels", "#dailycontent", "#artclass"],
    "cta": "Follow for the next idea.",
    "schedule_text": "",
    "daily": False,
    "timezone": settings.default_timezone,
}

def _clean_json(text: str) -> dict[str, Any]:
    text = text.strip()
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("No JSON object returned")
    return json.loads(text[start:end + 1])

def _normalize(package: dict[str, Any], prompt: str, timezone_name: str) -> dict[str, Any]:
    data = {**FALLBACK, **package}
    if data.get("platform") not in ALLOWED_PLATFORMS:
        data["platform"] = "instagram"
    if data.get("content_type") not in ALLOWED_TYPES:
        data["content_type"] = "reel"
    data["daily"] = bool(data.get("daily", False))
    data["timezone"] = data.get("timezone") or timezone_name
    try:
        data["duration_seconds"] = max(6, min(60, int(data.get("duration_seconds", 15))))
    except (TypeError, ValueError):
        data["duration_seconds"] = 15
    data["hashtags"] = [
        h if str(h).startswith("#") else f"#{h}"
        for h in (data.get("hashtags") or [])[:15]
    ]
    data["scenes"] = data.get("scenes") or []
    data["slides"] = data.get("slides") or []
    return data

def parse_schedule(schedule_text: str, timezone_name: str, now: datetime | None = None) -> str | None:
    if not schedule_text:
        return None
    base = now or datetime.now(timezone.utc)
    dt = parse_date(
        schedule_text,
        settings={
            "RELATIVE_BASE": base.replace(tzinfo=None),
            "RETURN_AS_TIMEZONE_AWARE": True,
            "TIMEZONE": timezone_name,
            "TO_TIMEZONE": "UTC",
            "PREFER_DATES_FROM": "future",
        },
    )
    if not dt:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat()

async def generate(
    prompt: str,
    style: str = "professional minimal",
    duration: int = 15,
    timezone_name: str | None = None,
) -> dict[str, Any]:
    tz_name = timezone_name or settings.default_timezone
    now_iso = datetime.now(timezone.utc).isoformat()
    user = f"""User brief: {prompt}
Preferred style: {style}
Default duration: {duration} seconds.
Default timezone: {tz_name}
Current UTC time: {now_iso}
Infer the best content type and platform from the brief.
Do not invent a schedule when none was requested."""
    try:
        async with httpx.AsyncClient(timeout=settings.ollama_timeout) as client:
            r = await client.post(
                f"{settings.ollama_base_url}/api/chat",
                json={
                    "model": settings.ollama_model,
                    "messages": [
                        {"role": "system", "content": SYSTEM},
                        {"role": "user", "content": user},
                    ],
                    "stream": False,
                    "options": {"temperature": 0.5},
                },
            )
            r.raise_for_status()
            package = _normalize(_clean_json(r.json()["message"]["content"]), prompt, tz_name)
    except Exception:
        package = _normalize(FALLBACK, prompt, tz_name)
        package["title"] = prompt[:70].strip() or package["title"]

    if not package.get("duration_seconds"):
        package["duration_seconds"] = duration
    package["scheduled_at"] = parse_schedule(package.get("schedule_text", ""), package["timezone"])
    return package
