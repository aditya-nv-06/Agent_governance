import json
import os

from dotenv import load_dotenv
from openai import APIStatusError, OpenAI

from .decision import ToolRequest
from .tools import TOOLS


load_dotenv()


class LLMQuotaError(RuntimeError):
    """The configured OpenAI project cannot spend API quota."""


class LLMServiceError(RuntimeError):
    """A provider failure that should not expose raw details to the client."""


SYSTEM_PROMPT = """
You are a customer support AI agent. Your only job is to propose one tool
request for the user's message.

Never execute a tool, approve an action, explain your decision, return
Markdown, or include text outside the JSON object. Governance will validate
your proposed request separately.

Available tools:

- faq_search: use for FAQs, refund policies, product/support information, and
  general help questions. Arguments: {"query": "string"}.

- send_email: use only when the user explicitly asks to send an email.
  Arguments: {"recipient": "string", "message": "string"}.

- customer_database: use only when the user asks for customer account or
  customer-record information. Arguments: {"customer_id": "CUST-001"}.

Return exactly one valid JSON object in this form:
{"tool_name": "faq_search | send_email | customer_database | unknown", "arguments": {}}

Use only the argument fields defined for the selected tool. If no tool applies,
return {"tool_name": "unknown", "arguments": {}}.
"""


def decide_with_llm(
    message: str,
) -> ToolRequest:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured")

    client = OpenAI(api_key=api_key)
    model = os.getenv("OPENAI_MODEL", "gpt-5-mini")

    try:
        response = client.responses.create(
            model=model,
            instructions=SYSTEM_PROMPT,
            input=message,
        )
    except APIStatusError as error:
        body = getattr(error, "body", None) or {}
        code = getattr(error, "code", None) or body.get("code")
        if error.status_code == 429 and code == "insufficient_quota":
            raise LLMQuotaError(
                "OpenAI API quota is unavailable. Add API billing or credits to the project that owns this key."
            ) from error
        raise LLMServiceError("The OpenAI decision service is currently unavailable") from error

    raw_output = response.output_text.strip()

    try:

        data = json.loads(raw_output)

    except json.JSONDecodeError:

        raise ValueError(
            "LLM returned invalid JSON"
        )

    tool_name = data.get("tool_name")

    arguments = data.get("arguments", {})

    if not isinstance(tool_name, str):
        raise ValueError(
            "Invalid tool_name returned by LLM"
        )

    if not isinstance(arguments, dict):
        raise ValueError(
            "Invalid arguments returned by LLM"
        )

    return ToolRequest(
        tool_name=tool_name,
        arguments=arguments,
    )

