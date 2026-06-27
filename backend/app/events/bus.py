from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any

from app.events.types import EventType

EventHandler = Callable[["Event"], Awaitable[None]]


@dataclass(slots=True)
class Event:
    type: EventType
    payload: dict[str, Any] = field(default_factory=dict)


class EventBus:
    def __init__(self) -> None:
        self._handlers: dict[EventType, list[EventHandler]] = {}

    def subscribe(self, event_type: EventType, handler: EventHandler) -> None:
        self._handlers.setdefault(event_type, []).append(handler)

    async def publish(self, event: Event) -> None:
        for handler in self._handlers.get(event.type, []):
            await handler(event)


event_bus = EventBus()
