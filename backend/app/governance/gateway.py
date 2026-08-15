from sqlalchemy.orm import Session

from ..agent.tools import get_tool, list_tools
from .evaluator import PolicyDecision, PolicyEvaluator


class GovernanceGateway:

    def __init__(self, db: Session):
        self.evaluator = PolicyEvaluator(db)

    def evaluate(
        self,
        agent_id,
        run_id,
        tool_request,
    ) -> PolicyDecision:
        """Evaluate an untrusted tool request. run_id is kept for traceability."""

        tool = get_tool(tool_request.tool_name)

        if not tool:

            return PolicyDecision(
                allowed=False,
                reason=f"Tool '{tool_request.tool_name}' is not registered",
                severity="HIGH",
                expected_tools=list_tools(),
                status="BLOCK",
            )

        return self.authorize_tool(
            agent_id=agent_id,
            tool_name=tool_request.tool_name,
            data_source=tool.data_source,
            action=tool.action,
            requires_approval=tool.requires_approval,
        )

    def authorize_tool(
        self,
        agent_id,
        tool_name: str,
        data_source: str | None = None,
        action: str | None = None,
        requires_approval: bool = False,
    ) -> PolicyDecision:

        return self.evaluator.check_tool(
            agent_id=agent_id,
            tool_name=tool_name,
            data_source=data_source,
            action=action,
            requires_approval=requires_approval,
        )
