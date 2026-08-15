from dataclasses import dataclass, field
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from ..agent.tools import get_tool
from ..models import Agent, AgentRun, BehaviorProfile


ALLOW = "ALLOW"
BLOCK = "BLOCK"
REQUIRE_APPROVAL = "REQUIRE_APPROVAL"


@dataclass
class PolicyDecision:

    allowed: bool

    reason: str

    severity: str = "NONE"

    expected_tools: list[str] = field(
        default_factory=list
    )

    warning: str | None = None

    finding_type: str = "UNAUTHORIZED_TOOL"
    requires_approval: bool = False
    status: str = "ALLOW"

    def __post_init__(self):
        if self.status == "ALLOW" and not self.allowed:
            self.status = BLOCK
        elif self.status == "ALLOW" and self.requires_approval:
            self.status = REQUIRE_APPROVAL


class PolicyEvaluator:

    def __init__(self, db: Session):

        self.db = db


    def check_tool(
        self,
        agent_id,
        tool_name: str,
        data_source: str | None = None,
        action: str | None = None,
        requires_approval: bool = False,
    ) -> PolicyDecision:

        # A request for an unregistered tool must be governed as a policy
        # violation, not allowed to turn into an application error later.
        tool = get_tool(tool_name)
        if not tool:
            return PolicyDecision(
                allowed=False,
                reason=f"Tool '{tool_name}' is not registered",
                severity="CRITICAL",
                finding_type="UNKNOWN_TOOL",
            )

        data_source = data_source or tool.data_source
        action = action or tool.action

        # -----------------------------------------
        # 1. Find agent
        # -----------------------------------------

        agent = (
            self.db.query(Agent)
            .filter(
                Agent.id == agent_id
            )
            .first()
        )

        if not agent:

            return PolicyDecision(
                allowed=False,
                reason="Agent does not exist",
                severity="CRITICAL",
                status=BLOCK,
            )


        # -----------------------------------------
        # 2. Check agent status
        # -----------------------------------------

        if agent.status != "active":

            return PolicyDecision(
                allowed=False,
                reason=(
                    f"Agent status is "
                    f"'{agent.status}'"
                ),
                severity="CRITICAL",
                status=BLOCK,
            )


        # -----------------------------------------
        # 3. Find behavior profile
        # -----------------------------------------

        profile = (
            self.db.query(BehaviorProfile)
            .filter(
                BehaviorProfile.agent_id == agent.id
            )
            .first()
        )

        if not profile:

            return PolicyDecision(
                allowed=False,
                reason=(
                    "Agent has no "
                    "behavior profile"
                ),
                severity="CRITICAL",
                status=BLOCK,
            )


        # -----------------------------------------
        # 4. Read allowed tools
        # -----------------------------------------

        allowed_tools = (
            profile.allowed_tools or []
        )


        # -----------------------------------------
        # 5. Check requested tool
        # -----------------------------------------

        if tool_name not in allowed_tools:

            return PolicyDecision(
                allowed=False,

                reason=(
                    f"Tool '{tool_name}' "
                    "is not authorized "
                    "for this agent"
                ),

                severity="HIGH",

                expected_tools=allowed_tools,
                status=BLOCK,
            )

        if data_source and data_source not in (profile.allowed_data_sources or []):
            return PolicyDecision(
                allowed=False,
                reason=f"Data source '{data_source}' is not authorized for this agent",
                severity="HIGH",
                expected_tools=profile.allowed_data_sources or [],
                status=BLOCK,
            )

        if action and action not in (profile.allowed_actions or []):
            return PolicyDecision(
                allowed=False,
                reason=f"Action '{action}' is not authorized for this agent",
                severity="HIGH",
                expected_tools=profile.allowed_actions or [],
                status=BLOCK,
            )

        today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        usage = (
            self.db.query(AgentRun)
            .filter(AgentRun.agent_id == agent.id, AgentRun.created_at >= today)
            .count()
        )
        if usage >= profile.max_llm_calls:
            return PolicyDecision(
                allowed=False,
                reason=f"Daily LLM-call limit reached ({usage}/{profile.max_llm_calls})",
                severity="CRITICAL",
                status=BLOCK,
            )

        usage_percent = (usage / profile.max_llm_calls) * 100
        warning = None
        if usage_percent >= profile.critical_threshold:
            warning = "CRITICAL"
        elif usage_percent >= profile.warning_threshold:
            warning = "WARNING"


        # -----------------------------------------
        # 6. Tool is allowed
        # -----------------------------------------

        return PolicyDecision(
            allowed=True,

            reason=(
                "High-risk action requires human approval"
                if requires_approval
                else "Tool is authorized by behavior profile"
            ),

            severity="HIGH" if requires_approval else "NONE",

            expected_tools=allowed_tools,
            warning=warning,
            requires_approval=requires_approval,
            status=REQUIRE_APPROVAL if requires_approval else ALLOW,
        )
