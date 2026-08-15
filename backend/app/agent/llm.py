import json
import os

from dotenv import load_dotenv
from openai import OpenAI

from .decision import ToolRequest


load_dotenv()


api_key = os.getenv("OPENAI_API_KEY")

model = os.getenv(
    "OPENAI_MODEL",
    "gpt-5-mini",
)

if not api_key:
    raise RuntimeError(
        "OPENAI_API_KEY is not configured"
    )


client = OpenAI(
    api_key=api_key
)


SYSTEM_PROMPT = """
You are a customer support AI agent.

Your job is to decide which tool should be requested
to satisfy the user's request.

IMPORTANT:

You DO NOT execute tools.

You only propose a tool request.

Available tools:

1. faq_search
   Purpose:
   Search the FAQ knowledge base.

   Arguments:
   {
       "query": "string"
   }

2. send_email
   Purpose:
   Send an email.

   Arguments:
   {
       "recipient": "string",
       "message": "string"
   }

3. customer_database
   Purpose:
   Retrieve customer information.

   Arguments:
   {
       "customer_id": "string"
   }

Return ONLY valid JSON.

The JSON must have this structure:

{
    "tool_name": "tool name",
    "arguments": {}
}

If none of the tools are appropriate,
return:

{
    "tool_name": "unknown",
    "arguments": {}
}
"""


def decide_with_llm(
    message: str,
) -> ToolRequest:

    response = client.responses.create(
        model=model,

        instructions=SYSTEM_PROMPT,

        input=message,
    )

    raw_output = response.output_text.strip()

    try:

        data = json.loads(raw_output)

    except json.JSONDecodeError:

        raise ValueError(
            "LLM returned invalid JSON"
        )

    tool_name = data.get(
        "tool_name"
    )

    arguments = data.get(
        "arguments",
        {}
    )

    if not isinstance(
        tool_name,
        str
    ):
        raise ValueError(
            "Invalid tool_name returned by LLM"
        )

    if not isinstance(
        arguments,
        dict
    ):
        raise ValueError(
            "Invalid arguments returned by LLM"
        )

    return ToolRequest(
        tool_name=tool_name,
        arguments=arguments,
    )