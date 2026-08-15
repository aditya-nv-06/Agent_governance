from sqlalchemy.orm import Session

from .evaluator import PolicyEvaluator


class GovernanceGateway:

    def __init__(self, db: Session):
        self.evaluator = PolicyEvaluator(db)

    def authorize_tool(
        self,
        agent_id,
        tool_name: str,
        data_source: str | None = None,
        action: str | None = None,
    ):

        return self.evaluator.check_tool(
            agent_id=agent_id,
            tool_name=tool_name,
            data_source=data_source,
            action=action,
        )
