from datetime import datetime, timezone

from sqlalchemy.orm import Session

from ..models import (
    Agent,
    AgentRun,
    Finding,
    Approval,
    ExecutionEvent,
    AuditEvent,
)

from ..governance.gateway import GovernanceGateway
from ..governance.evaluator import PolicyDecision

from .decision import default_arguments
from .executor import execute_tool
from .runtime import propose_tool_request
from .tools import get_tool, list_tools


class AgentService:

    def __init__(self, db: Session):
        self.db = db
        self.gateway = GovernanceGateway(db)

    # -----------------------------------------
    # Decide which tool the agent wants
    # -----------------------------------------

    def choose_tool(self, message: str) -> str:
        return propose_tool_request(message).tool_request.tool_name

    # -----------------------------------------
    # Execute agent run
    # -----------------------------------------

    def run(
        self,
        agent_id,
        run_id,
        message: str,
    ):

        agent = (
            self.db.query(Agent)
            .filter(
                Agent.id == agent_id
            )
            .first()
        )

        if not agent:
            raise ValueError(
                "Agent not found"
            )

        proposal = propose_tool_request(message)
        tool_request = proposal.tool_request
        tool_name = tool_request.tool_name
        tool = get_tool(tool_name)

        self.db.add(AuditEvent(
            agent_id=agent.id,
            run_id=run_id,
            finding_id=None,
            event_type="TOOL_REQUESTED",
            actor="agent",
            details={
                "tool": tool_name,
                "arguments": tool_request.arguments,
                "data_source": tool.data_source if tool else None,
                "action": tool.action if tool else None,
                "decided_by": proposal.source,
                "model": proposal.model,
            },
        ))

        # -------------------------------------
        # Governance check
        # -------------------------------------

        if not tool:

            # An unregistered proposal never reaches the executor.
            decision = PolicyDecision(
                allowed=False,
                reason=f"Tool '{tool_name}' is not registered",
                severity="HIGH",
                expected_tools=list_tools(),
            )

        else:

            decision = (
                self.gateway.authorize_tool(
                    agent_id=agent_id,
                    tool_name=tool_name,
                    data_source=tool.data_source,
                    action=tool.action,
                )
            )

        if decision.warning:
            self.db.add(AuditEvent(
                agent_id=agent.id,
                run_id=run_id,
                finding_id=None,
                event_type="WARNING_TRIGGERED",
                actor="governance",
                details={"level": decision.warning, "reason": decision.reason},
            ))

        # -------------------------------------
        # BLOCK
        # -------------------------------------

        if not decision.allowed:

            return self.block_action(
                agent=agent,
                run_id=run_id,
                tool_name=tool_name,
                decision=decision,
            )

        self.db.add(AuditEvent(
            agent_id=agent.id,
            run_id=run_id,
            finding_id=None,
            event_type="TOOL_ALLOWED",
            actor="governance",
            details={"tool": tool_name},
        ))

        # -------------------------------------
        # ALLOW
        # -------------------------------------

        return self.execute_tool(
            agent=agent,
            run_id=run_id,
            tool_name=tool_name,
            message=message,
            arguments=tool_request.arguments,
        )

    # -----------------------------------------
    # Handle blocked tool
    # -----------------------------------------

    def block_action(
        self,
        agent,
        run_id,
        tool_name,
        decision,
    ):

        # Finding
        finding = Finding(
            agent_id=agent.id,
            run_id=run_id,

            finding_type="UNAUTHORIZED_TOOL",

            severity=decision.severity,

            expected=", ".join(
                decision.expected_tools
            ),

            actual=tool_name,

            reason=decision.reason,

            status="open",
        )

        self.db.add(finding)

        self.db.flush()

        # Approval
        approval = Approval(
            finding_id=finding.id,

            status="PENDING",

            requested_by="agent",

            decided_by=None,

            decision_reason=None,
        )

        self.db.add(approval)
        self.db.flush()

        self.db.add(AuditEvent(
            agent_id=agent.id,
            run_id=run_id,
            finding_id=finding.id,
            event_type="FINDING_CREATED",
            actor="governance",
            details={"finding_type": finding.finding_type, "severity": finding.severity},
        ))
        self.db.add(AuditEvent(
            agent_id=agent.id,
            run_id=run_id,
            finding_id=finding.id,
            event_type="APPROVAL_REQUESTED",
            actor="governance",
            details={"approval_id": str(approval.id)},
        ))

        # Execution event
        execution_event = ExecutionEvent(
            run_id=run_id,

            agent_id=agent.id,

            event_type="TOOL_BLOCKED",

            tool_name=tool_name,

            status="BLOCKED",

            details={
                "reason": decision.reason,
                "severity": decision.severity,
            },
        )

        self.db.add(execution_event)

        # Audit event
        audit = AuditEvent(
            agent_id=agent.id,

            run_id=run_id,

            finding_id=finding.id,

            event_type="GOVERNANCE_BLOCK",

            actor="governance",

            details={
                "tool": tool_name,
                "reason": decision.reason,
                "severity": decision.severity,
            },
        )

        self.db.add(audit)

        # Update run
        run = (
            self.db.query(AgentRun)
            .filter(
                AgentRun.id == run_id
            )
            .first()
        )

        if run:
            run.status = "blocked"
            run.completed_at = datetime.now(timezone.utc)

        agent.status = "blocked"
        self.db.add(AuditEvent(
            agent_id=agent.id,
            run_id=run_id,
            finding_id=finding.id,
            event_type="AGENT_BLOCKED",
            actor="governance",
            details={"reason": decision.reason},
        ))

        self.db.commit()

        return {
            "status": "blocked",

            "message": (
                "Action blocked by "
                "governance policy."
            ),

            "tool": tool_name,

            "governance": "BLOCKED",

            "finding_id": str(
                finding.id
            ),

            "approval_id": str(
                approval.id
            ),
        }

    # -----------------------------------------
    # Execute allowed tool
    # -----------------------------------------

    def execute_tool(
        self,
        agent,
        run_id,
        tool_name,
        message,
        arguments=None,
    ):

        result = self._invoke_tool(tool_name, message, arguments)

        # -------------------------------------
        # Execution event
        # -------------------------------------

        execution_event = ExecutionEvent(
            run_id=run_id,

            agent_id=agent.id,

            event_type="TOOL_EXECUTED",

            tool_name=tool_name,

            status="SUCCESS",

            details={
                "message": message,
                "result": result,
            },
        )

        self.db.add(
            execution_event
        )

        # -------------------------------------
        # Audit event
        # -------------------------------------

        audit = AuditEvent(
            agent_id=agent.id,

            run_id=run_id,

            finding_id=None,

            event_type="TOOL_EXECUTION",

            actor="agent",

            details={
                "tool": tool_name,
                "status": "SUCCESS",
            },
        )

        self.db.add(audit)

        # -------------------------------------
        # Complete run
        # -------------------------------------

        run = (
            self.db.query(AgentRun)
            .filter(
                AgentRun.id == run_id
            )
            .first()
        )

        if run:
            run.status = "completed"
            run.completed_at = datetime.now(timezone.utc)

        self.db.add(AuditEvent(
            agent_id=agent.id,
            run_id=run_id,
            finding_id=None,
            event_type="RUN_COMPLETED",
            actor="agent",
            details={"tool": tool_name},
        ))

        self.db.commit()

        return {
            "status": "completed",

            "message": (
                "Agent action completed."
            ),

            "tool": tool_name,

            "governance": "ALLOWED",

            "result": result,
        }

    def execute_approved_action(
        self,
        agent_id,
        run_id,
        tool_name: str,
        approved_by: str,
        approval_id,
    ):
        """Execute only the tool captured in an approved finding."""
        agent = self.db.get(Agent, agent_id)
        run = self.db.get(AgentRun, run_id)
        if not agent or not run:
            raise ValueError("Agent run not found")

        result = self._invoke_tool(tool_name, run.input_message)
        self.db.add(ExecutionEvent(
            run_id=run.id,
            agent_id=agent.id,
            event_type="APPROVED_TOOL_EXECUTED",
            tool_name=tool_name,
            status="SUCCESS",
            details={"approval_id": str(approval_id), "result": result},
        ))
        self.db.add(AuditEvent(
            agent_id=agent.id,
            run_id=run.id,
            finding_id=None,
            event_type="APPROVED_ACTION_EXECUTED",
            actor=approved_by,
            details={"approval_id": str(approval_id), "tool": tool_name},
        ))
        run.status = "completed"
        run.completed_at = datetime.now(timezone.utc)
        self.db.commit()
        return {"status": "completed", "tool": tool_name, "result": result}

    @staticmethod
    def _invoke_tool(tool_name: str, message: str, arguments: dict | None = None):
        return execute_tool(
            tool_name=tool_name,
            arguments=arguments if arguments else default_arguments(tool_name, message),
        )
