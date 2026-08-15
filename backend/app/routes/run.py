import uuid

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from sqlalchemy.orm import Session

from ..database import get_db

from ..models import AgentRun, AuditEvent

from ..schemas import AgentRunRequest

from ..agent.service import AgentService


router = APIRouter(
    prefix="/runs",
    tags=["Runs"],
)


@router.post("")
def create_run(
    request: AgentRunRequest,
    db: Session = Depends(get_db),
):

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

    except Exception as error:

        run.status = "failed"

        db.commit()

        raise HTTPException(
            status_code=500,
            detail=str(error),
        )


@router.get("")
def get_runs(
    db: Session = Depends(get_db),
):

    runs = (
        db.query(AgentRun)
        .order_by(
            AgentRun.created_at.desc()
        )
        .all()
    )

    return [
        {
            "id": str(run.id),
            "agent_id": str(run.agent_id),
            "status": run.status,
            "input_message": run.input_message,
            "created_at": run.created_at,
            "completed_at": run.completed_at,
        }
        for run in runs
    ]

@router.post("/{run_id}/execute")
def execute_run(
    run_id: uuid.UUID,
    db: Session = Depends(get_db),
):

    run = (
        db.query(AgentRun)
        .filter(
            AgentRun.id == run_id
        )
        .first()
    )

    if not run:
        raise HTTPException(
            status_code=404,
            detail="Run not found",
        )

    service = AgentService(db)

    result = service.run(
        agent_id=run.agent_id,
        run_id=run.id,
        message=run.input_message,
    )

    return result
