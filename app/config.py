from __future__ import annotations
import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class Settings:
    api_key: str = os.getenv("ARTCLASS_API_KEY", "")
    worker_key: str = os.getenv("WORKER_KEY", "")
    public_base_url: str = os.getenv("PUBLIC_BASE_URL", "http://localhost:8000").rstrip("/")
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./data/artclass.db")
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
    ollama_model: str = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
    ollama_timeout: int = int(os.getenv("OLLAMA_TIMEOUT", "120"))
    video_width: int = int(os.getenv("VIDEO_WIDTH", "1080"))
    video_height: int = int(os.getenv("VIDEO_HEIGHT", "1920"))
    video_fps: int = int(os.getenv("VIDEO_FPS", "30"))
    scene_seconds: int = int(os.getenv("SCENE_SECONDS", "3"))
    media_dir: str = os.getenv("MEDIA_DIR", "./artifacts")
    media_store: str = os.getenv("MEDIA_STORE", "local").lower()
    github_token: str = os.getenv("GITHUB_TOKEN", "")
    github_repo: str = os.getenv("GITHUB_REPO", "")
    github_release_tag: str = os.getenv("GITHUB_RELEASE_TAG", "artclass-media")
    meta_graph_base: str = os.getenv("META_GRAPH_BASE", "https://graph.instagram.com").rstrip("/")
    meta_graph_version: str = os.getenv("META_GRAPH_VERSION", "v25.0")
    instagram_user_id: str = os.getenv("INSTAGRAM_USER_ID", "")
    instagram_access_token: str = os.getenv("INSTAGRAM_ACCESS_TOKEN", "")
    worker_interval_seconds: int = int(os.getenv("WORKER_INTERVAL_SECONDS", "30"))

settings = Settings()
