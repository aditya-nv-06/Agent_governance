import uuid

from sqlalchemy.orm import Session

from ..models import AuditEvent


class AuditService:

    def __init__(self, db: Session):
        self.db = db

    def record(
        self,
        agent_id: uuid.UUID,
        event_type: str,
        actor: str,
        run_id: uuid.UUID | None = None,
        finding_id: uuid.UUID | None = None,
        details: dict | None = None
    ):

        event = AuditEvent(
            agent_id=agent_id,
            run_id=run_id,
            finding_id=finding_id,
            event_type=event_type,
            actor=actor,
            details=details or {}
        )

        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)

        return event
