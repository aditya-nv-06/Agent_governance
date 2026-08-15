import uuid

from sqlalchemy.orm import Session

from ..models import Finding


class FindingService:

    def __init__(self, db: Session):
        self.db = db

    def create_finding(
        self,
        agent_id: uuid.UUID,
        run_id: uuid.UUID,
        finding_type: str,
        severity: str,
        expected: str,
        actual: str,
        reason: str
    ) -> Finding:

        finding = Finding(
            agent_id=agent_id,
            run_id=run_id,
            finding_type=finding_type,
            severity=severity,
            expected=expected,
            actual=actual,
            reason=reason,
            status="open"
        )

        self.db.add(finding)
        self.db.commit()
        self.db.refresh(finding)

        return finding
