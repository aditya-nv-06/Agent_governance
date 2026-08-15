from fastapi import (
    APIRouter,
    HTTPException,
)

from ..agent.runtime import propose_tool_request
from ..agent.tools import list_tools
from ..schemas import (
    AgentDecisionRequest,
    AgentDecisionResponse,
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
