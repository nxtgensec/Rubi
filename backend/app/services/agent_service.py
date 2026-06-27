from uuid import uuid4

from app.schemas.agent import AgentCreate, AgentRead


class AgentService:
    def __init__(self) -> None:
        self._agents: dict[str, AgentRead] = {}

    async def list_agents(self) -> list[AgentRead]:
        return list(self._agents.values())

    async def create_agent(self, payload: AgentCreate) -> AgentRead:
        agent = AgentRead(id=str(uuid4()), status="draft", **payload.model_dump())
        self._agents[agent.id] = agent
        return agent


agent_service = AgentService()
