#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.services.llm import generate_storyboard
from app.services.video import create_reel_video


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate ARTCLASS reels from a prompt")
    parser.add_argument("prompt", help="The prompt to create the reel from")
    parser.add_argument("--style", default="cinematic", help="Visual style")
    parser.add_argument("--duration", type=int, default=15, help="Video duration in seconds")
    parser.add_argument("--output", default="output/reel.mp4", help="Output video path")
    args = parser.parse_args()

    storyboard = generate_storyboard(args.prompt, style=args.style)
    output_path = create_reel_video(
        prompt=args.prompt,
        storyboard=storyboard,
        duration_seconds=args.duration,
        aspect_ratio="9:16",
    )
    print(json.dumps({"storyboard": storyboard, "video": output_path}, indent=2))


if __name__ == "__main__":
    main()
