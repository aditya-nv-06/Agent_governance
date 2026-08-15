import uuid

from sqlalchemy.orm import Session

from .gateway import GovernanceGateway
from .finding_service import FindingService
from .severity import calculate_severity
from .response import GovernanceResponseService


class GovernedExecutionService:

    def __init__(self, db: Session):
        self.db = db

        self.gateway = GovernanceGateway(db)

        self.findings = FindingService(db)

        self.response = GovernanceResponseService(db)

    def execute_tool(
        self,
        agent_id: uuid.UUID,
        run_id: uuid.UUID,
        tool_name: str,
        tool_function,
        *args,
        **kwargs
    ):

        # --------------------------------
        # 1. Ask governance for permission
        # --------------------------------

        decision = self.gateway.authorize_tool(
            agent_id=agent_id,
            tool_name=tool_name
        )

        # --------------------------------
        # 2. BLOCK
        # --------------------------------

        if not decision.allowed:

            severity = calculate_severity(
                "UNAUTHORIZED_TOOL"
            )

            result = self.response.handle_deviation(
                agent_id=agent_id,
                run_id=run_id,
                finding_type="UNAUTHORIZED_TOOL",
                severity=severity,
                expected="Tool must be authorized",
                actual=f"Requested tool: {tool_name}",
                reason=decision.reason
            )

            return {
                "status": "BLOCKED",
                "tool": tool_name,
                "severity": severity,
                "finding_id": str(
                    result["finding"].id
                ),
                "reason": decision.reason
            }

        # --------------------------------
        # 3. ALLOWED → execute
        # --------------------------------

        tool_result = tool_function(
            *args,
            **kwargs
        )

        return {
            "status": "ALLOWED",
            "tool": tool_name,
            "result": tool_result
        }
