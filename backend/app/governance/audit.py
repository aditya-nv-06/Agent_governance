import uuid

from sqlalchemy.orm import Session

from ..models import AuditEvent


class AuditService:

    def __init__(self, db: Session):
        self.db = db

    def record(
        self,
        agent_id: uuid.UUID | str,
        event_type: str,
        actor: str,
        run_id: uuid.UUID | str | None = None,
        finding_id: uuid.UUID | str | None = None,
        details: dict | None = None
    ):
        aid = uuid.UUID(str(agent_id)) if agent_id and not isinstance(agent_id, uuid.UUID) else agent_id
        rid = uuid.UUID(str(run_id)) if run_id and not isinstance(run_id, uuid.UUID) else run_id
        fid = uuid.UUID(str(finding_id)) if finding_id and not isinstance(finding_id, uuid.UUID) else finding_id

        event = AuditEvent(
            agent_id=aid,
            run_id=rid,
            finding_id=fid,
            event_type=event_type,
            actor=actor,
            details=details or {}
        )

        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)

        return event
