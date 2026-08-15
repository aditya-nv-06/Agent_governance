from typing import Callable


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


def customer_database(
    customer_id: str,
):

    return {
        "tool": "customer_database",
        "customer_id": customer_id,
        "name": "Demo Customer",
        "email": "customer@example.com",
    }


TOOLS: dict[str, Callable] = {

    "faq_search":
        faq_search,

    "send_email":
        send_email,

    "customer_database":
        customer_database,
}


def get_tool(
    tool_name: str,
):

    return TOOLS.get(
        tool_name
    )


def list_tools():

    return list(
        TOOLS.keys()
    )