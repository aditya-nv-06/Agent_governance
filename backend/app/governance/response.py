import uuid

from sqlalchemy.orm import Session

from .audit import AuditService
from .enforcement import EnforcementEngine
from .finding_service import FindingService


class GovernanceResponseService:

    def __init__(self, db: Session):

        self.db = db

        self.findings = FindingService(db)

        self.enforcement = EnforcementEngine(db)

        self.audit = AuditService(db)

    def handle_deviation(
        self,
        agent_id: uuid.UUID,
        run_id: uuid.UUID,
        finding_type: str,
        severity: str,
        expected: str,
        actual: str,
        reason: str
    ):

        # 1. Create finding
        finding = self.findings.create_finding(
            agent_id=agent_id,
            run_id=run_id,
            finding_type=finding_type,
            severity=severity,
            expected=expected,
            actual=actual,
            reason=reason
        )

        # 2. Record finding creation
        self.audit.record(
            agent_id=agent_id,
            run_id=run_id,
            finding_id=finding.id,
            event_type="FINDING_CREATED",
            actor="governance_engine",
            details={
                "finding_type": finding_type,
                "severity": severity
            }
        )

        # 3. Block
        action = self.enforcement.block(
            finding_id=finding.id,
            reason=reason
        )

        # 4. Audit block
        self.audit.record(
            agent_id=agent_id,
            run_id=run_id,
            finding_id=finding.id,
            event_type="TOOL_BLOCKED",
            actor="governance_engine",
            details={
                "action_id": str(action.id)
            }
        )

        return {
            "finding": finding,
            "action": action
        }
