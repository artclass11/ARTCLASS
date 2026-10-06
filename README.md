# ARTCLASS — AI Instagram Content Agent

Prompt -> professional Reel -> caption/hashtags -> schedule -> Instagram.

ARTCLASS is a local-first open-source content automation stack: give the agent one natural-language brief and it handles the content workflow.

## What it does

- Generates Reel scripts and captions with a local Ollama model.
- Renders a 9:16 Reel with FFmpeg and Pillow without paid video APIs.
- Publishes media through a public URL. Optional GitHub Release asset storage is included for free remote deployments.
- Schedules and publishes Reels through Instagram's official API.
- Exposes an MCP server so the capability can be packaged as a ChatGPT/Codex plugin.
- Includes a GitHub Actions worker that checks scheduled posts every 15 minutes.
- Includes a fallback content template so rendering still works when Ollama is offline.

The initial renderer is intentionally lightweight. For GPU-based AI visuals, the architecture can be extended with ComfyUI/Wan2.1 while keeping the same agent API.

## Open-source stack

Ollama provides a local API for open models. Change OLLAMA_MODEL to use another local model.
ComfyUI is an optional visual backend, and Wan2.1 is a practical open video model when a GPU is available. Kokoro can be added for local voice generation.

## Local run

1. Install FFmpeg.
2. Install and run Ollama, then pull a model such as llama3.2:3b.
3. Install dependencies: pip install -r requirements.txt
4. Copy .env.example to .env and set ARTCLASS_API_KEY.
5. Start: uvicorn app.main:app --reload

Open /docs to test the API.

## One-prompt API

POST /v1/create with:

{
  "prompt": "Make a 15 second premium Reel about 3 wedding photography tips",
  "style": "cinematic minimal",
  "duration": 15
}

The response returns a job_id. Poll GET /v1/jobs/{job_id} until status=ready.

Schedule with POST /v1/schedule or provide schedule_at in the create request.

## Instagram setup

Instagram publishing uses Meta's official publishing flow. Configure a Professional Instagram account and the required Meta/Instagram app permissions, then set INSTAGRAM_USER_ID and INSTAGRAM_ACCESS_TOKEN. META_GRAPH_BASE and META_GRAPH_VERSION are configurable.

The API needs a publicly reachable video URL at publishing time. MEDIA_STORE=github uses GitHub Release assets as a simple free media-hosting option.

## Free deployment path

Render supports free Python/Docker web services, but free instances have ephemeral local files and can spin down. The repository therefore supports GitHub Release asset media plus the GitHub Actions scheduler. For dependable long-running scheduling, use persistent Postgres/Supabase for the database.

## ChatGPT/Codex plugin

The plugin/ directory is a portable Agent Plugins package containing plugin.json, mcp.json, and the instagram-content skill.

Change the MCP URL in plugin/mcp.json after deploying app/mcp_server.py.

## Security

- Keep API keys and Meta tokens only in environment variables or managed secrets.
- The agent never needs an Instagram password.
- No login automation, CAPTCHA bypass, scraping, follow automation or mass-DM automation.
- Default behavior is schedule-first; immediate publishing should be explicit.
- Use HTTPS in production.
