from dataclasses import dataclass


@dataclass(frozen=True)
class ToolRequest:
    tool_name: str
    arguments: dict


def default_arguments(tool_name: str, message: str) -> dict:
    """Arguments used when no proposal is available, e.g. an approved replay."""
    if tool_name == "send_email":
        return {"recipient": "demo@example.com", "message": message}
    if tool_name == "customer_database":
        return {"customer_id": "CUST-001"}
    return {"query": message}


def decide_tool_request(message: str) -> ToolRequest:
    """Deterministic demo agent: decides, but never executes a tool."""
    text = message.lower()
    if "email" in text or "mail" in text:
        return ToolRequest("send_email", default_arguments("send_email", message))
    if "customer" in text or "database" in text:
        return ToolRequest("customer_database", default_arguments("customer_database", message))
    return ToolRequest("faq_search", {"query": message})
