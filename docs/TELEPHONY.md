# Telephony Setup

Rubi now has the platform flow needed for real phone calls:

1. A phone provider receives the call to your business number.
2. The provider sends an inbound webhook to Rubi.
3. Rubi creates a call session, selects the language, enables recording, and returns answer instructions.
4. The provider streams audio to the voice pipeline.
5. STT sends transcript turns back to Rubi.
6. The provider sends recording metadata after the call.

## Provider Webhook

Configure your provider to call:

```text
POST https://YOUR_PUBLIC_RUBI_API/api/v1/telephony/inbound
```

Example payload:

```json
{
  "provider": "exotel",
  "provider_call_id": "provider-call-id",
  "from_number": "+919000000001",
  "to_number": "+914000000001",
  "agent_id": "agent_default",
  "preferred_language": "te-IN"
}
```

The response includes:

- `action`: answer the call.
- `stream_url`: where the provider should send live audio.
- `recording_enabled`: whether the provider should record.
- `language`: selected language for the session.
- `greeting`: first spoken message.

Set `PUBLIC_VOICE_STREAM_BASE_URL` in `.env` to the public WebSocket base URL that your phone provider can reach.

## Supported Languages

The MVP config supports:

- Telugu: `te-IN`
- Indian English: `en-IN`
- Hindi: `hi-IN`
- Tamil: `ta-IN`
- Kannada: `kn-IN`
- Malayalam: `ml-IN`

The current language detector is intentionally lightweight and should be replaced by Faster Whisper language detection once streaming STT is wired in.

## What Access Is Needed For Live Calls

To connect a real number, Rubi needs one of:

- Twilio account SID, auth token, and phone number.
- Exotel SID, API token, API key, subdomain, and phone number.
- SIP/Asterisk server access, SIP trunk details, and routing rules.

Without those, the API and dashboard can be tested locally, but public phone calls cannot reach the machine.

## Twilio Setup

For your Twilio number, configure the voice webhook:

```text
POST {PUBLIC_BACKEND_URL}/api/v1/twilio/voice
```

Rubi returns TwiML that starts an interactive speech flow using Twilio `<Gather>`.
The agent asks for:

- Caller name
- Requirement
- Budget
- Whether the caller agrees to a team callback

Rubi also attempts to start Twilio call recording through the Twilio Recordings API.

The Twilio recording callback is:

```text
POST {PUBLIC_BACKEND_URL}/api/v1/twilio/recording
```

Local development still needs a public tunnel before Twilio can reach the backend.

## Stored Call Data

Rubi stores local call records in:

```text
data/rubi_store.json
```

Each record includes:

- Caller number
- Transcript turns
- Readable summary
- Name, need, budget
- Agreement state: `agreed`, `not_agreed`, or `collecting`
- Twilio recording URL when Twilio sends it

## Website Knowledge

Put your website/business content in:

```text
docs/business_knowledge.md
```

The intake agent uses this file when answering website-related questions. Replace the placeholder text with real service, pricing, FAQ, process, and contact details.
