from dataclasses import dataclass, field
from datetime import datetime, timezone

from sqlalchemy.orm import Session

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

    requires_approval: bool = False

    @property
    def status(self) -> str:

        if not self.allowed:
            return BLOCK

        if self.requires_approval:
            return REQUIRE_APPROVAL

        return ALLOW


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
            )

        if data_source and data_source not in (profile.allowed_data_sources or []):
            return PolicyDecision(
                allowed=False,
                reason=f"Data source '{data_source}' is not authorized for this agent",
                severity="HIGH",
                expected_tools=profile.allowed_data_sources or [],
            )

        if action and action not in (profile.allowed_actions or []):
            return PolicyDecision(
                allowed=False,
                reason=f"Action '{action}' is not authorized for this agent",
                severity="HIGH",
                expected_tools=profile.allowed_actions or [],
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
        )
