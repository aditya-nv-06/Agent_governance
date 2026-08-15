from fastapi import APIRouter, Depends

from sqlalchemy.orm import Session

from ..database import get_db
from ..auth import AdminUser, require_admin

from ..models import Agent, AuditEvent


router = APIRouter(
    prefix="/audit",
    tags=["Audit"],
)


@router.get("")
def get_audit_events(
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(require_admin),
):

    events = (
        db.query(AuditEvent)
        .join(Agent, AuditEvent.agent_id == Agent.id)
        .filter(Agent.owner_id == admin.id)
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


@router.get("/events", include_in_schema=False)
def get_audit_event_alias(db: Session = Depends(get_db)):
    return get_audit_events(db)
