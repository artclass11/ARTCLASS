import os
import tempfile
from pathlib import Path

os.environ["DATABASE_URL"] = "sqlite:///" + str(Path(tempfile.mkdtemp()) / "test.db")
os.environ["MEDIA_DIR"] = str(Path(tempfile.mkdtemp()))

from app.db import init_db, new_job, get_job, add_schedule, due_schedules
from app.content import _clean_json, _normalize, parse_schedule, FALLBACK
from app.video import render_single_image

def test_db_roundtrip():
    init_db()
    job_id = new_job("test prompt", {"style": "cinematic", "duration": 30})
    item = get_job(job_id)
    assert item["prompt"] == "test prompt"
    assert item["status"] == "queued"
    assert item["media_urls"] == []
    assert item["options"]["style"] == "cinematic"
    assert item["options"]["duration"] == 30

def test_content_json():
    payload = _clean_json('{"title":"x","scenes":[{"text":"hello","visual":"card"}]}')
    assert payload["title"] == "x"
    assert payload["scenes"][0]["text"] == "hello"

def test_content_normalization():
    data = _normalize({"platform": "bad", "content_type": "bad", "hashtags": ["reels"]}, "hello", "Asia/Kolkata")
    assert data["platform"] == "instagram"
    assert data["content_type"] == "reel"
    assert data["hashtags"][0] == "#reels"
    assert data["timezone"] == "Asia/Kolkata"

def test_schedule_parser():
    value = parse_schedule(
        "tomorrow at 7 PM",
        "Asia/Kolkata",
        now=__import__("datetime").datetime(2026, 10, 6, 10, 0, tzinfo=__import__("datetime").timezone.utc),
    )
    assert value and value.endswith("+00:00")

def test_schedule_claim_is_atomic():
    init_db()
    job_id = new_job("scheduled")
    add_schedule(job_id, "2000-01-01T00:00:00+00:00", False, "UTC")
    first = due_schedules()
    second = due_schedules()
    assert first and first[0]["job_id"] == job_id
    assert second == []

def test_fallback_shape():
    assert "scenes" in FALLBACK
    assert len(FALLBACK["hashtags"]) >= 4

def test_image_render():
    path = render_single_image({
        "title": "Test post",
        "hook": "A useful test",
        "caption": "This is a render test."
    })
    assert Path(path).exists()
    assert Path(path).suffix == ".jpg"
