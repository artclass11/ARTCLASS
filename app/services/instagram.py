from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

import requests

from app.config import settings


def schedule_instagram_post(file_path: str, caption: str, scheduled_at: Optional[str] = None, account_id: Optional[str] = None) -> dict:
    token = settings()["INSTAGRAM_ACCESS_TOKEN"]
    account = account_id or settings()["INSTAGRAM_ACCOUNT_ID"]
    api_version = settings()["INSTAGRAM_API_VERSION"]

    if not token or not account:
        return {
            "status": "not_configured",
            "message": "Set INSTAGRAM_ACCESS_TOKEN and INSTAGRAM_ACCOUNT_ID in your .env file before scheduling.",
        }

    media_url = f"https://graph.facebook.com/{api_version}/{account}/media"
    payload = {
        "caption": caption,
        "media_type": "VIDEO",
        "video_url": f"file://{file_path}",
        "access_token": token,
    }

    try:
        response = requests.post(media_url, data=payload, timeout=120)
        response.raise_for_status()
        result = response.json()
        return {
            "status": "scheduled",
            "result": result,
            "file_path": file_path,
        }
    except Exception as exc:
        return {
            "status": "error",
            "message": str(exc),
            "file_path": file_path,
        }
