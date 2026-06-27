from app.schemas.agent import AgentCreate, AgentRead
from app.services.agent_service import agent_service
from fastapi import APIRouter

router = APIRouter()


@router.get("", response_model=list[AgentRead])
async def list_agents() -> list[AgentRead]:
    return await agent_service.list_agents()


@router.post("", response_model=AgentRead, status_code=201)
async def create_agent(payload: AgentCreate) -> AgentRead:
    return await agent_service.create_agent(payload)
