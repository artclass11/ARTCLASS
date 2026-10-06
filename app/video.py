from __future__ import annotations
import re
import subprocess
import uuid
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from .config import settings

FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_REG = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

def _font(size: int, bold: bool = False):
    try:
        return ImageFont.truetype(FONT_BOLD if bold else FONT_REG, size)
    except Exception:
        return ImageFont.load_default()

def _safe(text: str) -> str:
    text = re.sub(r"[^a-zA-Z0-9_-]+", "-", text).strip("-")
    return (text or "reel")[:60]

def _wrap(draw, text: str, font, max_width: int):
    words = text.split()
    lines, current = [], ""
    for word in words:
        test = f"{current} {word}".strip()
        if draw.textbbox((0, 0), test, font=font)[2] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines or [""]

def render_card_reel(package: dict) -> str:
    out_dir = Path(settings.media_dir) / str(uuid.uuid4())
    out_dir.mkdir(parents=True, exist_ok=True)
    width, height = settings.video_width, settings.video_height
    scenes = package.get("scenes") or [{"text": package.get("hook", "ARTCLASS"), "visual": "minimal"}]

    for idx, scene in enumerate(scenes):
        img = Image.new("RGB", (width, height), (12, 12, 12))
        draw = ImageDraw.Draw(img)
        for x in range(0, width, 120):
            shade = 14 + ((x // 120) % 4) * 4
            draw.rectangle([x, 0, x + 90, height], fill=(shade, shade, shade))

        draw.rectangle([72, 100, 170, 108], fill=(245, 245, 245))
        draw.text((72, 145), "ARTCLASS", font=_font(34, True), fill=(230, 230, 230))

        y = 560
        title_font = _font(82, True)
        for line in _wrap(draw, str(scene.get("text", "")), title_font, width - 144):
            draw.text((72, y), line, font=title_font, fill=(255, 255, 255))
            y += 102

        visual = str(scene.get("visual", "")).strip()
        if visual:
            draw.text((72, height - 250), visual[:120], font=_font(28), fill=(175, 175, 175))

        draw.text(
            (width - 230, height - 105),
            f"{idx + 1:02d} / {len(scenes):02d}",
            font=_font(28, True),
            fill=(230, 230, 230),
        )
        img.save(out_dir / f"scene{idx:03d}.png", "PNG")

    output = out_dir / f"{_safe(package.get('title', 'reel'))}.mp4"
    cmd = [
        "ffmpeg", "-y",
        "-framerate", "1",
        "-i", str(out_dir / "scene%03d.png"),
        "-vf",
        f"scale={width}:{height},zoompan=z='min(zoom+0.0012,1.06)':d={settings.scene_seconds * settings.video_fps}:s={width}x{height}:fps={settings.video_fps},format=yuv420p",
        "-an",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "21",
        "-movflags", "+faststart",
        str(output),
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    return str(output)
