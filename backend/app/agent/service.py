from datetime import datetime, timezone

from sqlalchemy.orm import Session

from ..models import (
    Agent,
    AgentRun,
    ExecutionEvent,
    ResponseAction,
)

from ..governance.gateway import GovernanceGateway
from ..governance.evaluator import BLOCK, REQUIRE_APPROVAL
from ..governance.persistence import (
    create_approval,
    create_audit_event,
    create_execution_event,
    create_finding,
    create_response_action,
)

from .decision import default_arguments
from .executor import execute_tool
from .runtime import propose_tool_request
from .tools import get_tool


TOOL_REQUEST_EVENT = "LLM_TOOL_REQUEST"


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

        # The proposal is recorded before governance runs, so an approved
        # action can later replay exactly what the LLM asked for.
        create_execution_event(
            db=self.db,
            run_id=run_id,
            agent_id=agent.id,
            event_type=TOOL_REQUEST_EVENT,
            tool_name=tool_name,
            status="REQUESTED",
            details={
                "message": message,
                "arguments": tool_request.arguments,
                "decided_by": proposal.source,
                "model": proposal.model,
            },
        )

        create_audit_event(
            db=self.db,
            agent_id=agent.id,
            run_id=run_id,
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
        )

        # -------------------------------------
        # Governance check
        # -------------------------------------

        decision = self.gateway.evaluate(
            agent_id=agent_id,
            run_id=run_id,
            tool_request=tool_request,
        )

        if decision.warning:
            create_audit_event(
                db=self.db,
                agent_id=agent.id,
                run_id=run_id,
                event_type="WARNING_TRIGGERED",
                actor="governance",
                details={"level": decision.warning, "reason": decision.reason},
            )

        # -------------------------------------
        # BLOCK
        # -------------------------------------

        if decision.status == BLOCK:

            return self.block_action(
                agent=agent,
                run_id=run_id,
                tool_name=tool_name,
                decision=decision,
            )

        # -------------------------------------
        # REQUIRE APPROVAL
        # -------------------------------------

        if decision.status == REQUIRE_APPROVAL:

            return self.request_approval(
                agent=agent,
                run_id=run_id,
                tool_request=tool_request,
                decision=decision,
            )

        create_audit_event(
            db=self.db,
            agent_id=agent.id,
            run_id=run_id,
            event_type="TOOL_ALLOWED",
            actor="governance",
            details={"tool": tool_name},
        )

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

        finding = create_finding(
            db=self.db,
            agent_id=agent.id,
            run_id=run_id,
            tool_name=tool_name,
            severity=decision.severity,
            reason=decision.reason,
            expected=", ".join(decision.expected_tools),
        )

        create_response_action(
            db=self.db,
            finding_id=finding.id,
            action_type="BLOCK",
            status="EXECUTED",
            reason=decision.reason,
        )

        approval = create_approval(
            db=self.db,
            finding_id=finding.id,
            requested_by="agent",
        )

        create_audit_event(
            db=self.db,
            agent_id=agent.id,
            run_id=run_id,
            finding_id=finding.id,
            event_type="FINDING_CREATED",
            actor="governance",
            details={"finding_type": finding.finding_type, "severity": finding.severity},
        )
        create_audit_event(
            db=self.db,
            agent_id=agent.id,
            run_id=run_id,
            finding_id=finding.id,
            event_type="APPROVAL_REQUESTED",
            actor="governance",
            details={"approval_id": str(approval.id)},
        )

        create_execution_event(
            db=self.db,
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

        create_audit_event(
            db=self.db,
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
        create_audit_event(
            db=self.db,
            agent_id=agent.id,
            run_id=run_id,
            finding_id=finding.id,
            event_type="AGENT_BLOCKED",
            actor="governance",
            details={"reason": decision.reason},
        )

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
    # Authorized but high-risk: pause for approval
    # -----------------------------------------

    def request_approval(
        self,
        agent,
        run_id,
        tool_request,
        decision,
    ):
        """The tool is authorized, but a human must approve it before it runs."""

        tool_name = tool_request.tool_name

        finding = create_finding(
            db=self.db,
            agent_id=agent.id,
            run_id=run_id,
            tool_name=tool_name,
            severity=decision.severity,
            reason=decision.reason,
            finding_type="HIGH_RISK_ACTION",
            expected="High-risk actions require human approval",
        )

        create_response_action(
            db=self.db,
            finding_id=finding.id,
            action_type="REQUIRE_APPROVAL",
            status="PENDING",
            reason=decision.reason,
        )

        approval = create_approval(
            db=self.db,
            finding_id=finding.id,
            requested_by="agent",
        )

        create_execution_event(
            db=self.db,
            run_id=run_id,
            agent_id=agent.id,
            event_type="TOOL_PENDING_APPROVAL",
            tool_name=tool_name,
            status="PENDING_APPROVAL",
            details={
                "reason": decision.reason,
                "arguments": tool_request.arguments,
            },
        )

        create_audit_event(
            db=self.db,
            agent_id=agent.id,
            run_id=run_id,
            finding_id=finding.id,
            event_type="FINDING_CREATED",
            actor="governance",
            details={"finding_type": finding.finding_type, "severity": finding.severity},
        )

        create_audit_event(
            db=self.db,
            agent_id=agent.id,
            run_id=run_id,
            finding_id=finding.id,
            event_type="APPROVAL_REQUESTED",
            actor="governance",
            details={
                "approval_id": str(approval.id),
                "tool": tool_name,
                "severity": decision.severity,
            },
        )

        run = self.db.get(AgentRun, run_id)

        if run:
            run.status = "pending_approval"

        self.db.commit()

        return {
            "status": "pending_approval",
            "message": "High-risk action is waiting for human approval.",
            "tool": tool_name,
            "arguments": tool_request.arguments,
            "governance": "REQUIRE_APPROVAL",
            "reason": decision.reason,
            "severity": decision.severity,
            "finding_id": str(finding.id),
            "approval_id": str(approval.id),
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

        create_execution_event(
            db=self.db,
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

        create_audit_event(
            db=self.db,
            agent_id=agent.id,
            run_id=run_id,
            event_type="TOOL_EXECUTION",
            actor="agent",
            details={
                "tool": tool_name,
                "status": "SUCCESS",
            },
        )

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

        create_audit_event(
            db=self.db,
            agent_id=agent.id,
            run_id=run_id,
            event_type="RUN_COMPLETED",
            actor="agent",
            details={"tool": tool_name},
        )

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
        finding_id=None,
    ):
        """Execute only the tool captured in an approved finding."""
        agent = self.db.get(Agent, agent_id)
        run = self.db.get(AgentRun, run_id)
        if not agent or not run:
            raise ValueError("Agent run not found")

        arguments = self._requested_arguments(run.id, tool_name)
        result = self._invoke_tool(tool_name, run.input_message, arguments)
        create_execution_event(
            db=self.db,
            run_id=run.id,
            agent_id=agent.id,
            event_type="APPROVED_TOOL_EXECUTED",
            tool_name=tool_name,
            status="SUCCESS",
            details={
                "approval_id": str(approval_id),
                "arguments": arguments,
                "result": result,
            },
        )
        create_audit_event(
            db=self.db,
            agent_id=agent.id,
            run_id=run.id,
            event_type="APPROVED_ACTION_EXECUTED",
            actor=approved_by,
            details={"approval_id": str(approval_id), "tool": tool_name},
        )
        if finding_id:
            for action in (
                self.db.query(ResponseAction)
                .filter(
                    ResponseAction.finding_id == finding_id,
                    ResponseAction.status == "PENDING",
                )
                .all()
            ):
                action.status = "EXECUTED"

        run.status = "completed"
        run.completed_at = datetime.now(timezone.utc)
        self.db.commit()
        return {
            "status": "completed",
            "tool": tool_name,
            "arguments": arguments,
            "result": result,
        }

    def _requested_arguments(self, run_id, tool_name: str) -> dict | None:
        """Recover the arguments the agent originally proposed for this run."""

        event = (
            self.db.query(ExecutionEvent)
            .filter(
                ExecutionEvent.run_id == run_id,
                ExecutionEvent.event_type == TOOL_REQUEST_EVENT,
                ExecutionEvent.tool_name == tool_name,
            )
            .order_by(ExecutionEvent.created_at.desc())
            .first()
        )

        if not event:
            return None

        arguments = (event.details or {}).get("arguments")

        return arguments if isinstance(arguments, dict) else None

    @staticmethod
    def _invoke_tool(tool_name: str, message: str, arguments: dict | None = None):
        return execute_tool(
            tool_name=tool_name,
            arguments=arguments if arguments else default_arguments(tool_name, message),
        )
