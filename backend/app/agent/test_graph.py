from app.agent.graph import build_graph


graph = build_graph()


state = {
    "agent_id": "test-agent",
    "run_id": "test-run",
    "user_message": "I need customer information",
    "selected_tool": None,
    "tool_result": None,
    "decision": None,
    "error": None
}


result = graph.invoke(state)

print(result)
