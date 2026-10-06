# ARTCLASS

ARTCLASS is a prompt-to-video + scheduling agent for Instagram. It is built to create short-form reels from a single prompt, generate a storyboard with an open-source local LLM, render a video from scenes, and optionally publish it to Instagram using the Meta Graph API.

Key benefits:
- Prompt-driven video generation workflow
- Local open-source LLM support via Ollama
- Free/open-source stack for scripting and rendering
- Reel creation for 9:16 social video output
- Optional Instagram auto-scheduling through Meta API
- Daily content automation workflow

## What this MVP includes
- FastAPI backend for generation and scheduling
- Local story generation using Ollama
- Reel rendering with ffmpeg + PIL
- Instagram scheduling API adapter
- Command-line workflow for daily posting

## Quick start

1. Install dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. Install FFmpeg:
   - macOS: `brew install ffmpeg`
   - Ubuntu: `sudo apt-get install ffmpeg`

3. Install Ollama and pull a local model:
   ```bash
   ollama pull llama3.2
   ```

4. Copy the environment template:
   ```bash
   cp .env.example .env
   ```

5. Start the app:
   ```bash
   uvicorn app.main:app --reload
   ```

6. Generate a video:
   ```bash
   python scripts/generate_reel.py "A cinematic luxury lifestyle reel for a smart watch, dramatic lighting, upright composition, slow motion, social-first storytelling"
   ```

7. Schedule a post to Instagram (after you configure your access token):
   ```bash
   python scripts/schedule_instagram.py --file output/reel.mp4 --caption "Luxury tech, built for the next move."
   ```

## Architecture

- `app/services/llm.py` - local LLM storyboard generation via Ollama
- `app/services/video.py` - reel renderer with scenes, captions, and ffmpeg export
- `app/services/instagram.py` - Meta Graph API helper for Instagram posting
- `app/main.py` - API endpoints for prompt-to-video and scheduling
- `scripts/generate_reel.py` - CLI entry point
- `scripts/schedule_instagram.py` - scheduling utility

## Example prompt

> Cinematic luxury fitness ad for a premium smart watch, dramatic studio lighting, fluid motion, macro close-ups, ultra-clean framing, high contrast, CTA overlay, feel premium and futuristic.

## Notes

This repository is designed to be open-source and local-first. For more advanced, premium video generation like a heavy generative model stack (Higgsfield-style motion, stylized scenes, multi-shot cinematic phrasing), you can integrate SDXL/FLUX diffusion pipelines or video diffusion models on top of this architecture.

## License

MIT
