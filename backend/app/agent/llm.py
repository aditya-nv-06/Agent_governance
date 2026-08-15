import json
import os

from dotenv import load_dotenv
from openai import OpenAI

from .decision import ToolRequest
from .tools import TOOLS


load_dotenv()


DEFAULT_MODEL = "gpt-5-mini"


SYSTEM_PROMPT = """
You are a customer support AI agent.

Your job is to decide which tool should be requested
to satisfy the user's request.

IMPORTANT:

You DO NOT execute tools.

You only propose a tool request.

Available tools:

{tool_catalog}

Return ONLY valid JSON.

The JSON must have this structure:

{{
    "tool_name": "tool name",
    "arguments": {{}}
}}

If none of the tools are appropriate,
return:

{{
    "tool_name": "unknown",
    "arguments": {{}}
}}
"""


def _tool_catalog() -> str:

    entries = []

    for index, tool in enumerate(TOOLS.values(), start=1):

        arguments = ", ".join(
            f'"{name}": "string"'
            for name in tool.arguments
        )

        entries.append(
            f"{index}. {tool.name}\n"
            f"   Data source: {tool.data_source}\n"
            f"   Action: {tool.action}\n"
            f"   Arguments: {{{arguments}}}"
        )

    return "\n\n".join(entries)


def llm_model() -> str:

    return os.getenv("OPENAI_MODEL", DEFAULT_MODEL)


def llm_enabled() -> bool:

    return bool(os.getenv("OPENAI_API_KEY"))


def _client() -> OpenAI:

    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is not configured"
        )

    return OpenAI(api_key=api_key)


def decide_with_llm(message: str) -> ToolRequest:
    """Ask the LLM to propose a tool request. The proposal is untrusted."""

    response = _client().responses.create(
        model=llm_model(),
        instructions=SYSTEM_PROMPT.format(
            tool_catalog=_tool_catalog()
        ),
        input=message,
    )

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
