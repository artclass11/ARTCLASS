from __future__ import annotations

import os
import random
import subprocess
from pathlib import Path
from typing import Any, Dict, List

from PIL import Image, ImageDraw, ImageFont

from app.config import ensure_output_dir, settings


def _build_scene_image(scene_text: str, idx: int, width: int, height: int, palette: List[tuple]) -> Image.Image:
    img = Image.new("RGB", (width, height), palette[idx % len(palette)])
    draw = ImageDraw.Draw(img)

    for _ in range(40):
        x0 = random.randint(0, width)
        y0 = random.randint(0, height)
        x1 = x0 + random.randint(80, 220)
        y1 = y0 + random.randint(80, 220)
        color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        draw.ellipse((x0, y0, x1, y1), fill=color)

    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 120))
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")

    draw = ImageDraw.Draw(img)
    border = 80
    text_box = (border, height - 460, width - border, height - 90)
    draw.rounded_rectangle(text_box, radius=28, fill=(0, 0, 0, 180))

    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 72)
    except OSError:
        font = ImageFont.load_default()

    lines = [scene_text[i:i + 24] for i in range(0, len(scene_text), 24)]
    for i, line in enumerate(lines[:3]):
        y = text_box[1] + 35 + i * 90
        draw.text((text_box[0] + 30, y), line, fill=(255, 255, 255), font=font)

    return img


def _render_frames(storyboard: Dict[str, Any], output_dir: Path, duration_seconds: int) -> List[str]:
    scenes = storyboard.get("scenes", [])
    if not scenes:
        scenes = [{"caption": "AI-generated reel"}]

    frame_paths: List[str] = []
    width, height = 1080, 1920
    palette = [
        (24, 24, 42),
        (36, 54, 74),
        (52, 12, 40),
        (13, 52, 46),
        (82, 52, 18),
    ]

    frame_rate = 24
    total_frames = max(24, frame_rate * max(1, duration_seconds))
    per_scene_frames = max(1, total_frames // max(1, len(scenes)))

    for idx, scene in enumerate(scenes):
        text = scene.get("caption") or scene.get("shot") or "AI reel"
        for frame_index in range(per_scene_frames):
            frame = _build_scene_image(text, idx + frame_index, width, height, palette)
            filename = output_dir / f"frame_{idx}_{frame_index:03d}.png"
            frame.save(filename)
            frame_paths.append(str(filename))

    return frame_paths


def create_reel_video(prompt: str, storyboard: Dict[str, Any], duration_seconds: int = 15, aspect_ratio: str = "9:16") -> str:
    output_dir = Path(ensure_output_dir())
    slug = (
        "".join(ch for ch in prompt.lower() if ch.isalnum() or ch in [" ", "-"])
        .strip()
        .replace(" ", "-")[:80]
        or "artclass-reel"
    )
    frame_dir = output_dir / slug
    frame_dir.mkdir(exist_ok=True, parents=True)

    for existing in frame_dir.iterdir():
        if existing.is_file():
            existing.unlink()

    _render_frames(storyboard, frame_dir, duration_seconds)

    output_file = output_dir / f"{slug}.mp4"
    fps = 24
    frame_pattern = str(frame_dir / "frame_%d_%03d.png")
    cmd = [
        "ffmpeg",
        "-y",
        "-framerate",
        str(fps),
        "-i",
        str(frame_dir / "frame_%d_%03d.png"),
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        str(output_file),
    ]

    subprocess.run(cmd, check=True)
    return str(output_file)
