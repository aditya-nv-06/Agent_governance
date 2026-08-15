import uuid

from sqlalchemy.orm import Session

from ..models import Approval


class ApprovalService:

    def __init__(self, db: Session):
        self.db = db

    def request_approval(
        self,
        finding_id: uuid.UUID,
        requested_by: str
    ):

        approval = Approval(
            finding_id=finding_id,
            status="PENDING",
            requested_by=requested_by
        )

        self.db.add(approval)
        self.db.commit()
        self.db.refresh(approval)

        return approval

    def decide(
        self,
        approval_id: uuid.UUID,
        approved: bool,
        decided_by: str,
        reason: str,
    ):

        approval = self.db.get(
            Approval,
            approval_id
        )

        if not approval:
            raise ValueError(
                "Approval not found"
            )

        approval.status = (
            "APPROVED"
            if approved
            else "REJECTED"
        )

        approval.decided_by = decided_by
        approval.decision_reason = reason

        self.db.commit()
        self.db.refresh(approval)

        return approval
