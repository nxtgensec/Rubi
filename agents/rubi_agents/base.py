from dataclasses import dataclass, field


@dataclass(slots=True)
class AgentDefinition:
    name: str
    agent_type: str
    system_prompt: str
    language: str = "telugu"
    voice: str = "piper-te-IN"
    allowed_tools: list[str] = field(default_factory=list)
    knowledge_base_ids: list[str] = field(default_factory=list)
