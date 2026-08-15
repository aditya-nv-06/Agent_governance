from langgraph.graph import (
    StateGraph,
    START,
    END
)

from .state import AgentState


def agent_node(
    state: AgentState
):

    message = state[
        "user_message"
    ].lower()

    # -----------------------------
    # Mock agent decision
    # -----------------------------

    if "customer" in message:

        selected_tool = (
            "customer_database"
        )

    elif (
        "email" in message
        or "mail" in message
    ):

        selected_tool = "send_email"

    else:

        selected_tool = "faq_search"

    return {
        "selected_tool": selected_tool
    }


def build_graph():

    graph = StateGraph(
        AgentState
    )

    graph.add_node(
        "agent",
        agent_node
    )

    graph.add_edge(
        START,
        "agent"
    )

    graph.add_edge(
        "agent",
        END
    )

    return graph.compile()
