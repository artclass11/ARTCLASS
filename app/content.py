from __future__ import annotations
import json
from typing import Any
import httpx
from .config import settings

SYSTEM = """You are ARTCLASS, a professional short-form social content director.
Return ONLY valid JSON with keys: title, hook, scenes, voiceover, caption, hashtags, cta.
scenes must be an array of 4-7 objects with text and visual.
Style: premium, concise, original, useful. Avoid unsupported factual claims."""

FALLBACK = {
    "title": "Daily idea",
    "hook": "Here is one useful idea worth trying today.",
    "scenes": [
        {"text": "Start with one clear goal.", "visual": "minimal editorial title card"},
        {"text": "Show the useful detail quickly.", "visual": "clean motion card"},
        {"text": "Give one practical takeaway.", "visual": "bold takeaway card"},
        {"text": "Make the next step easy.", "visual": "simple call to action card"}
    ],
    "voiceover": "",
    "caption": "A simple idea, made useful. Save this for later.",
    "hashtags": ["#contentcreator", "#reels", "#instagramtips", "#dailycontent", "#artclass"],
    "cta": "Follow for the next idea."
}

def _clean_json(text: str) -> dict[str, Any]:
    text = text.strip()
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("No JSON object returned")
    return json.loads(text[start:end + 1])

async def generate(prompt: str, style: str = "premium minimal", duration: int = 15) -> dict[str, Any]:
    user = f"""Prompt: {prompt}
Style: {style}
Target duration: {duration} seconds.
Make each scene readable in a vertical Reel and avoid long paragraphs."""
    try:
        async with httpx.AsyncClient(timeout=settings.ollama_timeout) as client:
            r = await client.post(
                f"{settings.ollama_base_url}/api/chat",
                json={
                    "model": settings.ollama_model,
                    "messages": [
                        {"role": "system", "content": SYSTEM},
                        {"role": "user", "content": user}
                    ],
                    "stream": False,
                    "options": {"temperature": 0.7}
                }
            )
            r.raise_for_status()
            package = _clean_json(r.json()["message"]["content"])
            if not package.get("scenes"):
                raise ValueError("Model returned no scenes")
            return package
    except Exception:
        return {**FALLBACK, "title": prompt[:70].strip() or FALLBACK["title"]}
