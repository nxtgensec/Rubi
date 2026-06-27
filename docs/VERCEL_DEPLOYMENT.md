# Vercel Deployment

Use this for the Rubi dashboard frontend.

## Vercel Project Settings

- Framework preset: Next.js
- Root directory: `frontend`
- Build command: `npm run build`
- Install command: `npm install`
- Output directory: leave empty / default

## Frontend Environment Variables

Set this in Vercel Project Settings -> Environment Variables:

```text
NEXT_PUBLIC_API_URL=https://your-live-backend-domain.com
```

Do not put Twilio tokens, Supabase service-role keys, or other secrets in `NEXT_PUBLIC_` variables.
Anything prefixed with `NEXT_PUBLIC_` is visible in the browser.

## Backend Environment Variables

The FastAPI backend still needs its own live host unless you later convert all backend routes to Next.js API routes.
Set these on the backend host:

```text
PUBLIC_BACKEND_URL=https://your-live-backend-domain.com
PUBLIC_VOICE_STREAM_BASE_URL=wss://your-live-backend-domain.com/voice
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_PHONE_NUMBER=
SUPABASE_URL=
SUPABASE_SERVICE_ROLE_KEY=
CORS_ORIGINS=["https://your-vercel-app.vercel.app"]
```

For local development, keep using the root `.env` file.

## Twilio

After the backend is live and healthy, update Twilio Voice webhook:

```text
https://your-live-backend-domain.com/api/v1/twilio/voice
```

Keep Twilio webhook update as the last step so live calls do not point to a half-deployed backend.

## Safe Deploy Order

1. Deploy backend and confirm `/health` returns ok.
2. Deploy frontend on Vercel with `NEXT_PUBLIC_API_URL` pointing to the backend.
3. Confirm dashboard visitor counter and calls API load.
4. Update Twilio webhook to the live backend URL.
5. Make one test call.
