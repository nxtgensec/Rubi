# API

Base URL: `/api/v1`

## Implemented MVP Endpoints

- `POST /auth/login`
- `GET /agents`
- `POST /agents`
- `GET /calls`
- `GET /knowledge`
- `POST /knowledge/upload`
- `GET /tools`
- `GET /events/stream`
- `GET /metrics`
- `GET /health`
- `GET /telephony/languages`
- `GET /telephony/calls`
- `POST /telephony/inbound`
- `POST /telephony/outbound`
- `POST /telephony/calls/{call_id}/answer`
- `POST /telephony/calls/{call_id}/transcript`
- `POST /telephony/calls/{call_id}/recording`
- `POST /telephony/calls/{call_id}/end`
- `POST /twilio/voice`
- `POST /twilio/recording`
- `POST /twilio/status`
- `POST /twilio/outbound`

FastAPI generates OpenAPI documentation at `/docs`.

## Notes

Routes intentionally delegate to service classes. Business logic should stay out of routers as the platform grows.

## Telephony Provider Flow

1. Provider sends an inbound webhook to `POST /telephony/inbound`.
2. Rubi creates a call session, chooses the language, requests recording, and returns answer instructions.
3. Provider connects audio to the future voice stream URL.
4. STT posts transcript turns to `POST /telephony/calls/{call_id}/transcript`.
5. Provider posts recording metadata to `POST /telephony/calls/{call_id}/recording`.
6. Provider or Rubi ends the call with `POST /telephony/calls/{call_id}/end`.
