from dataclasses import dataclass
from typing import Callable


def faq_search(query: str):

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


@dataclass(frozen=True)
class Tool:
    """Registry metadata the governance evaluator enforces against a profile."""

    name: str
    function: Callable
    data_source: str
    action: str
    arguments: tuple[str, ...]
    requires_approval: bool = False


TOOLS: dict[str, Tool] = {

    "faq_search": Tool(
        name="faq_search",
        function=faq_search,
        data_source="faq_database",
        action="search",
        arguments=("query",),
    ),

    "send_email": Tool(
        name="send_email",
        function=send_email,
        data_source="email_service",
        action="send_email",
        arguments=("recipient", "message"),
        requires_approval=True,
    ),

    "customer_database": Tool(
        name="customer_database",
        function=customer_database,
        data_source="customer_database",
        action="read",
        arguments=("customer_id",),
        requires_approval=True,
    ),
}


def get_tool(tool_name: str) -> Tool | None:

    return TOOLS.get(tool_name)


def list_tools() -> list[str]:

    return list(TOOLS.keys())
