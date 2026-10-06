import os
import tempfile
from pathlib import Path

os.environ["DATABASE_URL"] = "sqlite:///" + str(Path(tempfile.mkdtemp()) / "test.db")

from app.db import init_db, new_job, get_job, add_schedule, due_schedules
from app.content import _clean_json, FALLBACK

def test_db_roundtrip():
    init_db()
    job_id = new_job("test prompt")
    item = get_job(job_id)
    assert item["prompt"] == "test prompt"
    assert item["status"] == "processing"

def test_content_json():
    payload = _clean_json('{"title":"x","scenes":[{"text":"hello","visual":"card"}]}')
    assert payload["title"] == "x"
    assert payload["scenes"][0]["text"] == "hello"

def test_schedule():
    init_db()
    job_id = new_job("scheduled")
    add_schedule(job_id, "2000-01-01T00:00:00+00:00", False, "UTC")
    due = due_schedules()
    assert due and due[0]["job_id"] == job_id

def test_fallback_shape():
    assert "scenes" in FALLBACK
    assert len(FALLBACK["hashtags"]) >= 5
