---
name: artclass-content-director
description: Turn one natural-language message into professional social content, optional video/image/carousel assets, captions and hashtags, and optionally schedule Instagram publishing.
---

# ARTCLASS Content Director

Use one user message as the source of truth.

## Single-message behavior

Examples:
- Make a premium 20-second Reel about wedding photography tips and post it tomorrow at 7 PM.
- Create a carousel explaining 24K vs 22K gold and schedule it daily at 10 AM.
- Write a LinkedIn launch post for my new AI app.
- Make an Instagram ad for my wedding album service, cinematic black-and-white.

The agent infers:
1. content type
2. target platform
3. tone and visual style
4. duration or number of slides
5. caption, hashtags and CTA
6. requested schedule and recurrence
7. whether publishing is supported automatically

## Execution

1. Call create_content with the full user message.
2. Poll get_content_status until ready or error.
3. Return the content/media URL plus caption and hashtags.
4. When a future Instagram schedule was clearly requested, allow the backend to create it automatically.
5. Never publish immediately unless the user explicitly asks to publish now.
6. If a generated content type has no automatic Instagram publisher, return the finished asset and say it is ready for manual publishing rather than pretending it was posted.

## Quality rules

- Original, professional copy.
- Clear hooks and mobile-readable text.
- Correct 9:16 framing for Reels and Stories.
- No fabricated facts.
- No copyrighted style imitation.
- Never automate Instagram login, CAPTCHA handling or scraping.
- Use official Instagram publishing endpoints only.
