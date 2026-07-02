# Sarvam Voice Setup

Rubi uses Sarvam for Telugu-only voice-agent behavior.

## Purpose

- Sarvam Chat handles Rubi's Telugu web-development intake decisions.
- Sarvam Text-to-Speech generates the Telugu woman voice played to callers.
- Twilio still handles phone calls, call recording, and speech capture through Gather.

## Required Environment Variables

```text
SARVAM_API_KEY=
SARVAM_CHAT_MODEL=sarvam-30b
SARVAM_TTS_MODEL=bulbul:v3
SARVAM_TTS_SPEAKER=kavitha
```

For local Twilio testing, `PUBLIC_BACKEND_URL` must be a public HTTPS tunnel URL:

```text
PUBLIC_BACKEND_URL=https://your-active-tunnel.trycloudflare.com
```

For Vercel, add the same variables in Project Settings > Environment Variables.

## Behavior Note

Rubi is instructed to speak only in polite, clear Telugu. It should handle only web-development topics such as websites, ecommerce, landing pages, dashboards, CRM/admin panels, hosting, domains, SEO basics, payment integrations, and maintenance. Unknown or unrelated questions should be marked for team callback.

## Latency Note

This implementation still uses Twilio Gather. It is faster than the earlier flow, but it is not true real-time streaming. For real-time interruption and very low latency, migrate to Twilio Media Streams or ConversationRelay with streaming STT/TTS.
