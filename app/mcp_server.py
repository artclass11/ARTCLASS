from __future__ import annotations
import os
import requests
from mcp.server.fastmcp import FastMCP

BASE = os.getenv("ARTCLASS_API_URL", "http://localhost:8000").rstrip("/")
API_KEY = os.getenv("ARTCLASS_API_KEY", "")
WORKER_KEY = os.getenv("WORKER_KEY", "")

mcp = FastMCP("ARTCLASS")

def _headers():
    return {"X-API-Key": API_KEY}

@mcp.tool()
def create_reel(prompt: str, style: str = "premium minimal", duration: int = 15) -> dict:
    """Create a Reel from one natural-language prompt."""
    r = requests.post(
        f"{BASE}/v1/create",
        headers=_headers(),
        json={"prompt": prompt, "style": style, "duration": duration},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()

@mcp.tool()
def get_reel_status(job_id: str) -> dict:
    """Check Reel rendering status and return the public video URL when ready."""
    r = requests.get(f"{BASE}/v1/jobs/{job_id}", headers=_headers(), timeout=30)
    r.raise_for_status()
    return r.json()

@mcp.tool()
def schedule_reel(job_id: str, scheduled_at: str, daily: bool = False, timezone: str = "UTC") -> dict:
    """Schedule an existing Reel for Instagram publishing."""
    r = requests.post(
        f"{BASE}/v1/schedule",
        headers=_headers(),
        json={"job_id": job_id, "scheduled_at": scheduled_at, "daily": daily, "timezone": timezone},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()

@mcp.tool()
def run_due_posts() -> dict:
    """Publish due scheduled Reels through the official Instagram API."""
    r = requests.post(
        f"{BASE}/v1/worker/run",
        headers=_headers(),
        json={"worker_key": WORKER_KEY},
        timeout=120,
    )
    r.raise_for_status()
    return r.json()

if __name__ == "__main__":
    mcp.run(transport="streamable-http")
