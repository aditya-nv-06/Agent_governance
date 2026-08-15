from dataclasses import dataclass


@dataclass(frozen=True)
class ToolRequest:
    tool_name: str
    arguments: dict


def decide_tool_request(message: str) -> ToolRequest:
    """Deterministic demo agent: decides, but never executes a tool."""
    text = message.lower()
    if "email" in text or "mail" in text:
        return ToolRequest("send_email", {"recipient": "demo@example.com", "message": message})
    if "customer" in text or "database" in text:
        return ToolRequest("customer_database", {"customer_id": "CUST-001"})
    return ToolRequest("faq_search", {"query": message})
