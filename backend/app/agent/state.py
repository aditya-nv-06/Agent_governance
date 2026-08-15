from typing import TypedDict


class AgentState(TypedDict):

    user_message: str

    selected_tool: str | None

    tool_result: str | None

    decision: str | None

    error: str | None
