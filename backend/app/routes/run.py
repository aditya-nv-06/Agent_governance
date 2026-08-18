import uuid

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from sqlalchemy.orm import Session

from ..database import get_db
from ..auth import AdminUser, get_owned_agent, require_admin

from ..models import Agent, AgentRun, AuditEvent, ExecutionEvent

from ..schemas import AgentRunRequest

from ..agent.service import AgentService
from ..agent.llm import LLMQuotaError, LLMServiceError
from ..agent.tools import get_tool


router = APIRouter(
    prefix="/runs",
    tags=["Runs"],
)


@router.post("")
def create_run(
    request: AgentRunRequest,
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(require_admin),
):
    get_owned_agent(db, request.agent_id, admin)

    run = AgentRun(
        agent_id=request.agent_id,
        input_message=request.message,
        status="running",
    )

    db.add(run)
    db.commit()
    db.refresh(run)

    db.add(AuditEvent(
        agent_id=run.agent_id,
        run_id=run.id,
        finding_id=None,
        event_type="AGENT_RUN_STARTED",
        actor="agent",
        details={"message": run.input_message},
    ))
    db.commit()

    service = AgentService(db)

    try:

        result = service.run(
            agent_id=request.agent_id,
            run_id=run.id,
            message=request.message,
        )

        return {
            "run_id": str(run.id),
            **result,
        }

    except LLMQuotaError as error:
        run.status = "failed"
        db.commit()
        raise HTTPException(status_code=503, detail=str(error)) from error
    except (LLMServiceError, ValueError) as error:
        run.status = "failed"
        db.commit()
        raise HTTPException(status_code=502, detail=str(error)) from error
    except Exception as error:

        run.status = "failed"

        db.commit()

        raise HTTPException(
            status_code=500,
            detail=str(error),
        ) from error


@router.get("")
def get_runs(
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(require_admin),
):
    runs = (
        db.query(AgentRun)
        .order_by(
            AgentRun.created_at.desc()
        )
        .limit(250)
        .all()
    )
    if not runs:
        return []

    run_ids = [r.id for r in runs]
    events = (
        db.query(ExecutionEvent)
        .filter(
            ExecutionEvent.run_id.in_(run_ids),
            ExecutionEvent.event_type == "LLM_TOOL_REQUEST",
        )
        .all()
    )
    event_by_run = {e.run_id: e for e in events}

    response = []
    for run in runs:
        request_event = event_by_run.get(run.id)
        tool = get_tool(request_event.tool_name) if request_event and request_event.tool_name else None
        response.append({
            "id": str(run.id),
            "agent_id": str(run.agent_id),
            "status": run.status,
            "input_message": run.input_message,
            "created_at": run.created_at.isoformat() if run.created_at else None,
            "completed_at": run.completed_at.isoformat() if run.completed_at else None,
            "tool_name": request_event.tool_name if request_event else None,
            "data_source": tool.data_source if tool else None,
            "action": tool.action if tool else None,
        })
    return response

@router.post("/{run_id}/execute")
def execute_run(
    run_id: uuid.UUID,
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(require_admin),
):

    run = (
        db.query(AgentRun)
        .filter(
            AgentRun.id == run_id,
        )
        .first()
    )

    if not run:
        raise HTTPException(
            status_code=404,
            detail="Run not found",
        )
    get_owned_agent(db, run.agent_id, admin)

    service = AgentService(db)

    result = service.run(
        agent_id=run.agent_id,
        run_id=run.id,
        message=run.input_message,
    )

    return result
