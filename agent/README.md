# ARTCLASS agent behavior

One natural-language prompt is the main control surface.

Examples:
- Make a 20-second premium Reel about why 24K gold is different and schedule it tomorrow at 10 AM.
- Create a daily 7 PM Reel for the next 7 days about wedding photography tips.
- Make a minimal finance Reel about Apple earnings and schedule it for tonight.

Workflow:
1. Extract topic, tone, duration and publish timing.
2. Create the Reel package.
3. Poll status until ready or failed.
4. Schedule when a future time is requested.
5. Never publish immediately unless the user explicitly requests it.
6. Return the video URL, caption and schedule status.

Content rules:
- Concise hooks and readable vertical scenes.
- Original copy.
- Avoid fabricated claims.
- Official Instagram API only.
- Never automate Instagram login or scrape Instagram.
