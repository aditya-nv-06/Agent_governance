from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from sqlalchemy.orm import Session

from ..agent.runtime import propose_tool_request
from ..agent.service import AgentService
from ..agent.tools import list_tools
from ..database import get_db
from ..models import AgentRun
from ..schemas import (
    AgentDecisionRequest,
    AgentDecisionResponse,
    AgentRunInRunRequest,
)


router = APIRouter(
    prefix="/agent",
    tags=["Agent"],
)


@router.get("/tools")
def tools():

    return {"tools": list_tools()}


@router.post(
    "/decide",
    response_model=AgentDecisionResponse,
)
def decide(request: AgentDecisionRequest):
    """Return the agent's tool proposal only. Nothing is executed here."""

    try:

        proposal = propose_tool_request(request.message)

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error),
        )

    return AgentDecisionResponse(
        tool_name=proposal.tool_request.tool_name,
        arguments=proposal.tool_request.arguments,
        source=proposal.source,
    )


@router.post("/run")
def run_agent(
    request: AgentRunInRunRequest,
    db: Session = Depends(get_db),
):
    """Run the agent inside an existing run: LLM proposes, governance decides."""

    run = db.get(AgentRun, request.run_id)

    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    if run.agent_id != request.agent_id:
        raise HTTPException(status_code=400, detail="Run belongs to another agent")

    try:

        return AgentService(db).run(
            agent_id=request.agent_id,
            run_id=run.id,
            message=request.message,
        )

    except ValueError as error:

        db.rollback()

        raise HTTPException(status_code=400, detail=str(error)) from error

    except Exception as error:

        db.rollback()

        raise HTTPException(status_code=500, detail=str(error)) from error
