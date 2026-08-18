def main():
    from app.agent.llm import decide_with_llm

    try:
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
    except Exception as e:
        print("LLM test skipped or failed:", e)


if __name__ == "__main__":
    main()