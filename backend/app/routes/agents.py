import uuid
import logging
from fastapi import APIRouter, Depends

from sqlalchemy.orm import Session

from ..database import get_db

from ..auth import AdminUser, get_owned_agent, require_admin
from ..models import Agent, AgentRun, Approval, AuditEvent, BehaviorProfile, ExecutionEvent, Finding, ResponseAction

from ..schemas import AgentCreate, AgentResponse

from fastapi import (
    APIRouter,
    HTTPException,
)

from ..agent.llm import decide_with_llm
from ..agent.llm import LLMQuotaError, LLMServiceError
from ..schemas import (
    AgentDecisionRequest,
    AgentDecisionResponse,
)

router = APIRouter(
    prefix="/agents",
    tags=["Agents"],
)

logger = logging.getLogger(__name__)


@router.get(
    "",
    response_model=list[AgentResponse],
)
def get_agents(
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(require_admin),
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
    admin: AdminUser = Depends(require_admin),
):
    if payload.profile is None:
        raise HTTPException(status_code=400, detail="An agent cannot be created without a behavior profile.")

    agent = Agent(name=payload.name, description=payload.description, owner_id=admin.id)
    db.add(agent)
    db.flush()

    profile = BehaviorProfile(agent_id=agent.id, **payload.profile.model_dump())
    db.add(profile)
    db.commit()
    db.refresh(agent)
    return agent


@router.delete("/{agent_id}", status_code=204)
def delete_agent(
    agent_id: uuid.UUID,
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(require_admin),
):
    try:
        logger.info("Delete agent requested: admin=%s agent_id=%s", admin.email, agent_id)
        agent = db.get(Agent, agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        if agent.owner_id and agent.owner_id != admin.id:
            raise HTTPException(status_code=403, detail="Not authorized to delete this agent")

        finding_ids = [item[0] for item in db.query(Finding.id).filter(Finding.agent_id == agent.id).all()]
        if finding_ids:
            db.query(Approval).filter(Approval.finding_id.in_(finding_ids)).delete(synchronize_session=False)
            db.query(ResponseAction).filter(ResponseAction.finding_id.in_(finding_ids)).delete(synchronize_session=False)
        db.query(AuditEvent).filter(AuditEvent.agent_id == agent.id).delete(synchronize_session=False)
        db.query(ExecutionEvent).filter(ExecutionEvent.agent_id == agent.id).delete(synchronize_session=False)
        db.query(Finding).filter(Finding.agent_id == agent.id).delete(synchronize_session=False)
        db.query(AgentRun).filter(AgentRun.agent_id == agent.id).delete(synchronize_session=False)
        db.query(BehaviorProfile).filter(BehaviorProfile.agent_id == agent.id).delete(synchronize_session=False)
        db.delete(agent)
        db.commit()
        logger.info("Agent deleted: admin=%s agent=%s", admin.email, agent.id)
    except HTTPException:
        raise
    except Exception as error:
        logger.exception("Failed to delete agent %s for admin %s", agent_id, getattr(admin, "email", None))
        raise HTTPException(status_code=500, detail=str(error)) from error

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

    except LLMQuotaError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except (RuntimeError, LLMServiceError) as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error
    except Exception:
        # Do not leak provider configuration or stack details to callers.
        raise HTTPException(status_code=502, detail="Unable to obtain an LLM decision")
