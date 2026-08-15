import uuid

from sqlalchemy.orm import Session

from ..models import ResponseAction
from .finding_service import FindingService


class EnforcementEngine:

    def __init__(self, db: Session):
        self.db = db
        self.finding_service = FindingService(db)

    def block(
        self,
        finding_id: uuid.UUID,
        reason: str
    ):

        action = ResponseAction(
            finding_id=finding_id,
            action_type="BLOCK",
            status="EXECUTED",
            reason=reason
        )

        self.db.add(action)
        self.db.commit()
        self.db.refresh(action)

        return action
