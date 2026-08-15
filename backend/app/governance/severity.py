def calculate_severity(
    finding_type: str
) -> str:

    severity_map = {

        "UNAUTHORIZED_TOOL":
            "HIGH",

        "NO_BEHAVIOR_PROFILE":
            "CRITICAL",

        "POLICY_VIOLATION":
            "MEDIUM",

    }

    return severity_map.get(
        finding_type,
        "MEDIUM"
    )
