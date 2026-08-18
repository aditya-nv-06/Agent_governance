import os
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from ..models import (
    Agent,
    AgentRun,
    Finding,
    Approval,
    ResponseAction,
    ExecutionEvent,
    AuditEvent,
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

from .decision import ToolRequest, decide_tool_request
from .executor import execute_tool
from .llm import LLMQuotaError, LLMServiceError, decide_with_llm
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
        return self._choose_tool_request(message).tool_name

    @staticmethod
    def _choose_tool_request(message: str) -> ToolRequest:
        """Use the LLM decision layer unless explicitly disabled for tests."""
        if os.getenv("USE_LLM_DECISIONS", "true").lower() in {"0", "false", "no"}:
            return decide_tool_request(message)
        return decide_with_llm(message)

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

        fallback_reason = None
        try:
            tool_request = self._choose_tool_request(message)
        except (LLMQuotaError, LLMServiceError) as error:
            # Keep the governed demo available when the external decision
            # provider is unavailable. This never bypasses policy checks.
            tool_request = decide_tool_request(message)
            fallback_reason = str(error)
        tool_name = tool_request.tool_name
        tool = get_tool(tool_name)

        # -------------------------------------
        # Governance check
        # -------------------------------------

        decision = (
            self.gateway.authorize_tool(
                agent_id=agent_id,
                tool_name=tool_name,
                data_source=tool.data_source if tool else None,
                action=tool.action if tool else None,
            )
        )

        create_audit_event(
            db=self.db,
            agent_id=agent.id,
            run_id=run_id,
            event_type="TOOL_REQUESTED",
            actor="agent",
            details={
                "tool": tool_name,
                "data_source": tool.data_source if tool else None,
                "action": tool.action if tool else None,
            },
        )
        self.db.add(ExecutionEvent(
            run_id=run_id,
            agent_id=agent.id,
            event_type="LLM_TOOL_REQUEST",
            tool_name=tool_name,
            status="REQUESTED",
            details={"arguments": tool_request.arguments},
        ))
        if fallback_reason:
            self.db.add(AuditEvent(
                agent_id=agent.id,
                run_id=run_id,
                finding_id=None,
                event_type="LLM_DECISION_FALLBACK",
                actor="governance",
                details={"reason": fallback_reason, "tool": tool_name},
            ))

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
        self.db.add(ExecutionEvent(
            run_id=run_id,
            agent_id=agent.id,
            event_type="TOOL_ALLOWED",
            tool_name=tool_name,
            status="ALLOWED",
            details={},
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

        finding = create_finding(
            db=self.db,
            agent_id=agent.id,
            run_id=run_id,
            tool_name=tool_name,
            finding_type=decision.finding_type,
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

        self.db.add(finding)
        self.db.flush()

        create_audit_event(
            db=self.db,
            agent_id=agent.id,
            run_id=run_id,
            finding_id=finding.id,
            event_type="FINDING_CREATED",
            actor="governance",
            details={"finding_type": finding.finding_type, "severity": finding.severity},
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
            event_type="TOOL_BLOCKED",
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
                f"Action directly blocked by governance policy (out of scope): {decision.reason}"
            ),
            "tool": tool_name,
            "governance": "BLOCKED",
            "finding_id": str(
                finding.id
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

            finding_id=None,

            event_type="TOOL_EXECUTED",

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
        finding_id,
    ):
        """Execute the original request after a human has approved it."""
        agent = self.db.get(Agent, agent_id)
        run = self.db.get(AgentRun, run_id)
        if not agent or not run:
            raise ValueError("Agent run not found")

        # Recover the exact recorded request. Never accept fresh arguments or
        # ask the LLM to make a second decision after human approval.
        original_request = (
            self.db.query(ExecutionEvent)
            .filter(
                ExecutionEvent.run_id == run.id,
                ExecutionEvent.event_type == "LLM_TOOL_REQUEST",
            )
            .first()
        )
        if not original_request:
            raise ValueError("Original tool request was not recorded")
        request = ToolRequest(
            tool_name=original_request.tool_name or "",
            arguments=original_request.details.get("arguments", {}),
        )
        if request.tool_name != tool_name:
            raise ValueError("Approved tool does not match the original request")
        if not get_tool(request.tool_name):
            raise ValueError(f"Tool '{request.tool_name}' does not exist")

        result = self._execute_request(request.tool_name, request.arguments)
        self.db.add(ExecutionEvent(
            run_id=run.id,
            agent_id=agent.id,
            event_type="APPROVED_TOOL_EXECUTION",
            tool_name=request.tool_name,
            status="SUCCESS",
            details={
                "approval_id": str(approval_id),
                "arguments": request.arguments,
                "result": result,
            },
        ))
        create_audit_event(
            db=self.db,
            agent_id=agent.id,
            run_id=run.id,
            finding_id=finding_id,
            event_type="APPROVED_ACTION_EXECUTED",
            actor=approved_by,
            details={"approval_id": str(approval_id), "tool": request.tool_name},
        )
        run.status = "completed"
        run.completed_at = datetime.now(timezone.utc)
        self.db.commit()
        return {"status": "completed", "tool": request.tool_name, "result": result}

    @staticmethod
    def _invoke_tool(tool_name: str, message: str, arguments: dict | None = None):
        if arguments is not None:
            request = ToolRequest(tool_name=tool_name, arguments=arguments)
        else:
            request = decide_tool_request(message)
        if request.tool_name != tool_name:
            raise ValueError("Tool does not match the original request")
        return AgentService._execute_request(tool_name, request.arguments)

    @staticmethod
    def _execute_request(tool_name: str, arguments: dict):
        return execute_tool(tool_name, arguments)
