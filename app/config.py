from __future__ import annotations

import os
from typing import Any, Dict


def get_env(name: str, default: str = "") -> str:
    return os.getenv(name, default)


def ensure_output_dir() -> str:
    output_dir = get_env("MEDIA_OUTPUT_DIR", "output")
    os.makedirs(output_dir, exist_ok=True)
    return output_dir


def settings() -> Dict[str, str]:
    return {
        "OLLAMA_BASE_URL": get_env("OLLAMA_BASE_URL", "http://localhost:11434"),
        "OLLAMA_MODEL": get_env("OLLAMA_MODEL", "llama3.2"),
        "MEDIA_OUTPUT_DIR": get_env("MEDIA_OUTPUT_DIR", "output"),
        "INSTAGRAM_ACCESS_TOKEN": get_env("INSTAGRAM_ACCESS_TOKEN", ""),
        "INSTAGRAM_ACCOUNT_ID": get_env("INSTAGRAM_ACCOUNT_ID", ""),
        "INSTAGRAM_API_VERSION": get_env("INSTAGRAM_API_VERSION", "v19.0"),
    }
