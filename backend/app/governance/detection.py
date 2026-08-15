import uuid

from sqlalchemy.orm import Session

from ..models import BehaviorProfile, Finding


def create_tool_deviation(
    db: Session,
    agent_id: uuid.UUID,
    run_id: uuid.UUID,
    tool_name: str,
    profile: BehaviorProfile
) -> Finding:

    finding = Finding(
        agent_id=agent_id,
        run_id=run_id,
        finding_type="UNAUTHORIZED_TOOL",
        severity="HIGH",
        expected=(
            f"Allowed tools: "
            f"{profile.allowed_tools}"
        ),
        actual=f"Requested tool: {tool_name}",
        reason=(
            f"Tool '{tool_name}' is outside "
            "the approved behavior profile"
        ),
        status="open"
    )

    db.add(finding)
    db.commit()
    db.refresh(finding)

    return finding
