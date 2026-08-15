from fastapi import APIRouter, Depends

from sqlalchemy.orm import Session

from ..database import get_db

from ..models import Agent

from ..schemas import AgentCreate, AgentResponse

from fastapi import (
    APIRouter,
    HTTPException,
)

from ..agent.llm import decide_with_llm
from ..schemas import (
    AgentDecisionRequest,
    AgentDecisionResponse,
)

router = APIRouter(
    prefix="/agents",
    tags=["Agents"],
)


@router.get(
    "",
    response_model=list[AgentResponse],
)
def get_agents(
    db: Session = Depends(get_db),
):

    return (
        db.query(Agent)
        .order_by(Agent.name)
        .all()
    )


@router.post("", response_model=AgentResponse, status_code=201)
def create_agent(
    payload: AgentCreate,
    db: Session = Depends(get_db),
):
    agent = Agent(**payload.model_dump())
    db.add(agent)
    db.commit()
    db.refresh(agent)
    return agent

@router.post(
    "/decide",
    response_model=AgentDecisionResponse,
)
def decide(
    request: AgentDecisionRequest,
):

    try:

        result = decide_with_llm(
            request.message
        )

        return AgentDecisionResponse(
            tool_name=result.tool_name,
            arguments=result.arguments,
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error),
        )