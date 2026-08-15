from fastapi import APIRouter, Depends

from sqlalchemy.orm import Session

from ..database import get_db

from ..models import AuditEvent


router = APIRouter(
    prefix="/audit",
    tags=["Audit"],
)


@router.get("")
def get_audit_events(
    db: Session = Depends(get_db),
):

    events = (
        db.query(AuditEvent)
        .order_by(
            AuditEvent.created_at.desc()
        )
        .all()
    )

    return [
        {
            "id": str(event.id),
            "agent_id": str(event.agent_id),
            "run_id": (
                str(event.run_id)
                if event.run_id
                else None
            ),
            "finding_id": (
                str(event.finding_id)
                if event.finding_id
                else None
            ),
            "event_type": event.event_type,
            "actor": event.actor,
            "details": event.details,
            "created_at": event.created_at,
        }
        for event in events
    ]
