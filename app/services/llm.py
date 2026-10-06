from __future__ import annotations

import json
import re
from typing import Any, Dict, List

import requests

from app.config import settings


def _fallback_storyboard(prompt: str, style: str = "cinematic") -> Dict[str, Any]:
    return {
        "style": style,
        "title": "AI Reel Plan",
        "hook": "Hook the viewer in the first 2 seconds.",
        "scenes": [
            {"shot": "Open on the product or subject", "caption": "A striking first frame that stops the scroll."},
            {"shot": "Build energy with a transition", "caption": "Create momentum with quick motion and a sharp visual reveal."},
            {"shot": "Deliver the payoff", "caption": "End with a clear value proposition and CTA."},
        ],
        "prompt": prompt,
    }


def generate_storyboard(prompt: str, style: str = "cinematic") -> Dict[str, Any]:
    base_url = settings()["OLLAMA_BASE_URL"]
    model = settings()["OLLAMA_MODEL"]

    payload = {
        "model": model,
        "prompt": (
            "You are a viral reel strategist. Create a JSON object with keys: title, hook, scenes. "
            "The 'scenes' field is a list of 3-5 objects with 'shot' and 'caption'. "
            "The tone is " + style + ". Here is the content brief: " + prompt
        ),
        "stream": False,
        "format": "json",
    }

    try:
        response = requests.post(f"{base_url}/api/generate", json=payload, timeout=120)
        response.raise_for_status()
        data = response.json()
        raw = data.get("response", "")
        if raw:
            cleaned = raw.strip()
            try:
                return json.loads(cleaned)
            except json.JSONDecodeError:
                match = re.search(r"\{.*\}", cleaned, re.S)
                if match:
                    return json.loads(match.group(0))
        return _fallback_storyboard(prompt, style)
    except Exception:
        return _fallback_storyboard(prompt, style)
