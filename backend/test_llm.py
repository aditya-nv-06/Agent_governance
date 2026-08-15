from app.agent.llm import decide_with_llm


result = decide_with_llm(
    "What is your refund policy?"
)

print(
    "Tool:",
    result.tool_name
)

print(
    "Arguments:",
    result.arguments
)