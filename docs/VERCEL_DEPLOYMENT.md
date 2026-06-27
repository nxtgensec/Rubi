# Vercel Deployment

Use this for deploying Rubi from the monorepo with Vercel Services.

## Vercel Project Settings

- Framework preset: Services
- Root directory: `./`
- `vercel.json` defines:
  - `frontend` at `/`
  - `backend` at `/_/backend`

## Frontend Environment Variables

For the bundled Vercel Services deployment, set this in Vercel Project Settings -> Environment Variables:

```text
NEXT_PUBLIC_API_URL=/_/backend
```

If you later deploy the backend somewhere else, change it to that full backend URL instead.

Do not put Twilio tokens, Supabase service-role keys, or other secrets in `NEXT_PUBLIC_` variables.
Anything prefixed with `NEXT_PUBLIC_` is visible in the browser.

## Backend Environment Variables

Set these in Vercel Project Settings -> Environment Variables for the backend service:

```text
PUBLIC_BACKEND_URL=https://your-vercel-domain.vercel.app/_/backend
PUBLIC_VOICE_STREAM_BASE_URL=wss://your-vercel-domain.vercel.app/_/backend/voice
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_PHONE_NUMBER=
SUPABASE_URL=
SUPABASE_SERVICE_ROLE_KEY=
CORS_ORIGINS=["https://your-vercel-domain.vercel.app"]
```

For local development, keep using the root `.env` file.

## Twilio

After the backend is live and healthy, update Twilio Voice webhook:

```text
https://your-vercel-domain.vercel.app/_/backend/api/v1/twilio/voice
```

Keep Twilio webhook update as the last step so live calls do not point to a half-deployed backend.

## Safe Deploy Order

1. Deploy Vercel Services and confirm `/_/backend/health` returns ok.
2. Confirm frontend dashboard loads and `NEXT_PUBLIC_API_URL` points to `/_/backend`.
3. Confirm dashboard visitor counter and calls API load.
4. Update Twilio webhook to the live backend URL.
5. Make one test call.
