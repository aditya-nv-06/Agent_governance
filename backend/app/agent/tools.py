from dataclasses import dataclass
from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class ToolDefinition:
    """A registered demo tool and the policy metadata used to govern it."""

    function: Callable
    data_source: str
    action: str


def faq_search(
    query: str,
):

    return {
        "tool": "faq_search",
        "query": query,
        "result": (
            f"FAQ result for: {query}"
        ),
    }


def send_email(
    recipient: str,
    message: str,
):

    return {
        "tool": "send_email",
        "recipient": recipient,
        "message": message,
        "result": (
            "Email sent successfully"
        ),
    }


def customer_database(customer_id: str):

    return {
        "tool": "customer_database",
        "customer_id": customer_id,
        "name": "Demo Customer",
        "email": "customer@example.com",
    }


TOOLS: dict[str, ToolDefinition] = {
    "faq_search": ToolDefinition(
        function=faq_search,
        data_source="faq_database",
        action="read",
    ),
    "send_email": ToolDefinition(
        function=send_email,
        data_source="email_service",
        action="send_email",
    ),
    "customer_database": ToolDefinition(
        function=customer_database,
        data_source="customer_database",
        action="read",
    ),
}


def get_tool(tool_name: str) -> Tool | None:

    return TOOLS.get(tool_name)


def list_tools() -> list[str]:

    return list(
        TOOLS.keys()
    )
