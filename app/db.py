from __future__ import annotations
import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from .config import settings

def _path() -> str:
    url = settings.database_url
    if not url.startswith("sqlite:///"):
        raise RuntimeError("Starter database currently supports sqlite:/// only")
    path = url.removeprefix("sqlite:///")
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    return path

def connect() -> sqlite3.Connection:
    c = sqlite3.connect(_path(), timeout=30, isolation_level=None)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA journal_mode=WAL")
    c.execute("PRAGMA busy_timeout=30000")
    return c

def init_db() -> None:
    c = connect()
    c.executescript("""
    CREATE TABLE IF NOT EXISTS jobs (
      id TEXT PRIMARY KEY,
      prompt TEXT NOT NULL,
      status TEXT NOT NULL,
      title TEXT,
      caption TEXT,
      hashtags TEXT,
      script_json TEXT,
      video_path TEXT,
      video_url TEXT,
      error TEXT,
      media_type TEXT,
      media_urls TEXT,
      content_type TEXT,
      platform TEXT,
      options_json TEXT,
      created_at TEXT NOT NULL,
      updated_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS schedules (
      id TEXT PRIMARY KEY,
      job_id TEXT NOT NULL,
      scheduled_at TEXT NOT NULL,
      daily INTEGER NOT NULL DEFAULT 0,
      timezone TEXT NOT NULL DEFAULT 'UTC',
      status TEXT NOT NULL DEFAULT 'scheduled',
      published_media_id TEXT,
      last_error TEXT,
      created_at TEXT NOT NULL,
      FOREIGN KEY(job_id) REFERENCES jobs(id)
    );
    """)
    for col, ddl in [
        ("media_type", "ALTER TABLE jobs ADD COLUMN media_type TEXT"),
        ("media_urls", "ALTER TABLE jobs ADD COLUMN media_urls TEXT"),
        ("content_type", "ALTER TABLE jobs ADD COLUMN content_type TEXT"),
        ("platform", "ALTER TABLE jobs ADD COLUMN platform TEXT"),
        ("options_json", "ALTER TABLE jobs ADD COLUMN options_json TEXT"),
    ]:
        try:
            c.execute(ddl)
        except sqlite3.OperationalError:
            pass
    c.close()

def now() -> str:
    return datetime.now(timezone.utc).isoformat()

def new_job(prompt: str, options: dict | None = None) -> str:
    job_id = str(uuid.uuid4())
    ts = now()
    c = connect()
    c.execute(
        "INSERT INTO jobs(id,prompt,status,options_json,created_at,updated_at) VALUES(?,?,?,?,?,?)",
        (job_id, prompt, "queued", json.dumps(options or {}), ts, ts),
    )
    c.close()
    return job_id

def claim_job(job_id: str) -> bool:
    c = connect()
    cur = c.execute(
        "UPDATE jobs SET status='processing', updated_at=? WHERE id=? AND status='queued'",
        (now(), job_id),
    )
    c.close()
    return cur.rowcount == 1

def queued_jobs(limit: int = 3) -> list[dict]:
    c = connect()
    rows = c.execute(
        "SELECT * FROM jobs WHERE status='queued' ORDER BY created_at LIMIT ?",
        (limit,),
    ).fetchall()
    c.close()
    return [dict(r) for r in rows]

def claim_queued_jobs(limit: int = 3) -> list[dict]:
    c = connect()
    c.execute("BEGIN IMMEDIATE")
    try:
        rows = c.execute(
            "SELECT * FROM jobs WHERE status='queued' ORDER BY created_at LIMIT ?",
            (limit,),
        ).fetchall()
        items = [dict(r) for r in rows]
        for item in items:
            c.execute(
                "UPDATE jobs SET status='processing', updated_at=? WHERE id=? AND status='queued'",
                (now(), item["id"]),
            )
        c.execute("COMMIT")
        return items
    except Exception:
        c.execute("ROLLBACK")
        raise
    finally:
        c.close()

def update_job(job_id: str, **fields: Any) -> None:
    fields["updated_at"] = now()
    allowed = {"status","title","caption","hashtags","script_json","video_path","video_url","error",
                "media_type","media_urls","content_type","platform","options_json","updated_at"}
    fields = {k:v for k,v in fields.items() if k in allowed}
    if not fields:
        return
    sets = ",".join(f"{k}=?" for k in fields)
    vals = list(fields.values()) + [job_id]
    c = connect()
    c.execute(f"UPDATE jobs SET {sets} WHERE id=?", vals)
    c.close()

def get_job(job_id: str) -> dict | None:
    c = connect()
    row = c.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
    c.close()
    if not row:
        return None
    d = dict(row)
    d["script"] = json.loads(d.pop("script_json")) if d.get("script_json") else None
    d["hashtags"] = json.loads(d["hashtags"]) if d.get("hashtags") else []
    d["media_urls"] = json.loads(d["media_urls"]) if d.get("media_urls") else []
    try:
        d["options"] = json.loads(d["options_json"]) if d.get("options_json") else {}
        if not isinstance(d["options"], dict):
            d["options"] = {}
    except (TypeError, ValueError, json.JSONDecodeError):
        d["options"] = {}
    return d

def add_schedule(job_id: str, scheduled_at: str, daily: bool, timezone_name: str) -> str:
    schedule_id = str(uuid.uuid4())
    c = connect()
    c.execute(
        "INSERT INTO schedules(id,job_id,scheduled_at,daily,timezone,status,created_at) VALUES(?,?,?,?,?,?,?)",
        (schedule_id, job_id, scheduled_at, int(daily), timezone_name, "scheduled", now()),
    )
    c.close()
    return schedule_id

def claim_due_schedules(limit: int = 10) -> list[dict]:
    c = connect()
    c.execute("BEGIN IMMEDIATE")
    try:
        rows = c.execute(
            """SELECT s.*, j.video_url, j.caption, j.media_type, j.media_urls, j.content_type, j.platform
               FROM schedules s JOIN jobs j ON j.id=s.job_id
               WHERE s.status='scheduled' AND s.scheduled_at<=?
               ORDER BY s.scheduled_at LIMIT ?""",
            (now(), limit),
        ).fetchall()
        items = [dict(r) for r in rows]
        for item in items:
            c.execute("UPDATE schedules SET status='processing' WHERE id=?", (item["id"],))
        c.execute("COMMIT")
        return items
    except Exception:
        c.execute("ROLLBACK")
        raise
    finally:
        c.close()

def due_schedules(limit: int = 10) -> list[dict]:
    return claim_due_schedules(limit)

def mark_schedule(schedule_id: str, status: str, **fields: Any) -> None:
    allowed = {"status","published_media_id","last_error","scheduled_at"}
    fields["status"] = status
    fields = {k:v for k,v in fields.items() if k in allowed}
    sets = ",".join(f"{k}=?" for k in fields)
    vals = list(fields.values()) + [schedule_id]
    c = connect()
    c.execute(f"UPDATE schedules SET {sets} WHERE id=?", vals)
    c.close()
