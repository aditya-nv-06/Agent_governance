from .tools import get_tool


def execute_tool(
    tool_name: str,
    arguments: dict,
):
    """Execute a registered tool. Only governance may reach this function."""

    tool = get_tool(tool_name)

    if not tool:

        raise ValueError(
            f"Tool '{tool_name}' does not exist"
        )

    try:

        result = tool.function(
            **arguments
        )

    except TypeError as error:

        raise ValueError(
            f"Invalid arguments for "
            f"tool '{tool_name}': {error}"
        )

    return result

