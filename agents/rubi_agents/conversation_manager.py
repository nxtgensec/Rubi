from dataclasses import dataclass, field

from rubi_agents.base import AgentDefinition


@dataclass(slots=True)
class ConversationTurn:
    role: str
    content: str


@dataclass(slots=True)
class ConversationState:
    call_id: str
    caller_id: str
    agent: AgentDefinition
    turns: list[ConversationTurn] = field(default_factory=list)
    interrupted: bool = False


class ConversationManager:
    def __init__(self, state: ConversationState) -> None:
        self.state = state

    async def receive_transcript(self, text: str) -> None:
        self.state.turns.append(ConversationTurn(role="user", content=text))

    async def record_assistant_response(self, text: str) -> None:
        self.state.turns.append(ConversationTurn(role="assistant", content=text))

    async def interrupt(self) -> None:
        self.state.interrupted = True
