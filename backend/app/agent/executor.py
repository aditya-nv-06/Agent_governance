from .tools import get_tool


def execute_tool(
    tool_name: str,
    arguments: dict,
):

    tool = get_tool(
        tool_name
    )

    if not tool:

        raise ValueError(
            f"Tool '{tool_name}' does not exist"
        )

    try:

        result = tool(
            **arguments
        )

    except TypeError as error:

        raise ValueError(
            f"Invalid arguments for "
            f"tool '{tool_name}': {error}"
        )

    return result