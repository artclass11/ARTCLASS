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
    c.close()

def now() -> str:
    return datetime.now(timezone.utc).isoformat()

def new_job(prompt: str) -> str:
    job_id = str(uuid.uuid4())
    ts = now()
    c = connect()
    c.execute("INSERT INTO jobs(id,prompt,status,created_at,updated_at) VALUES(?,?,?,?,?)",
              (job_id, prompt, "processing", ts, ts))
    c.close()
    return job_id

def update_job(job_id: str, **fields: Any) -> None:
    fields["updated_at"] = now()
    allowed = {"status","title","caption","hashtags","script_json","video_path","video_url","error","updated_at"}
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

def due_schedules(limit: int = 10) -> list[dict]:
    c = connect()
    rows = c.execute(
      """SELECT s.*, j.video_url, j.caption
         FROM schedules s JOIN jobs j ON j.id=s.job_id
         WHERE s.status='scheduled' AND s.scheduled_at<=?
         ORDER BY s.scheduled_at LIMIT ?""", (now(), limit)
    ).fetchall()
    c.close()
    return [dict(r) for r in rows]

def mark_schedule(schedule_id: str, status: str, **fields: Any) -> None:
    allowed = {"status","published_media_id","last_error","scheduled_at"}
    fields["status"] = status
    fields = {k:v for k,v in fields.items() if k in allowed}
    sets = ",".join(f"{k}=?" for k in fields)
    vals = list(fields.values()) + [schedule_id]
    c = connect()
    c.execute(f"UPDATE schedules SET {sets} WHERE id=?", vals)
    c.close()
