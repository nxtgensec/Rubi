from pydantic import BaseModel, Field


class AgentBase(BaseModel):
    name: str
    agent_type: str = "general_assistant"
    language: str = "telugu"
    voice: str = "piper-te-IN"
    system_prompt: str
    allowed_tools: list[str] = Field(default_factory=list)
    knowledge_base_ids: list[str] = Field(default_factory=list)


class AgentCreate(AgentBase):
    pass


class AgentRead(AgentBase):
    id: str
    status: str = "draft"
