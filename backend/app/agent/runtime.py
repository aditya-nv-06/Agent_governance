import logging
from dataclasses import dataclass

from .decision import ToolRequest, decide_tool_request
from .llm import decide_with_llm, llm_enabled, llm_model

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AgentProposal:
    """An untrusted tool proposal. Governance decides whether it may run."""

    tool_request: ToolRequest
    source: str
    model: str | None


def propose_tool_request(message: str) -> AgentProposal:
    """Ask the LLM for a tool proposal, falling back to the rule-based agent."""

    if not llm_enabled():
        return AgentProposal(
            tool_request=decide_tool_request(message),
            source="rules",
            model=None,
        )

    try:
        tool_request = decide_with_llm(message)

    except Exception as error:
        logger.warning("LLM decision failed, using rule-based agent: %s", error)

        return AgentProposal(
            tool_request=decide_tool_request(message),
            source="rules_fallback",
            model=llm_model(),
        )

    return AgentProposal(
        tool_request=tool_request,
        source="llm",
        model=llm_model(),
    )
