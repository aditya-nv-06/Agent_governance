from sqlalchemy.orm import Session

from ..models import (
    Approval,
    AuditEvent,
    ExecutionEvent,
    Finding,
    ResponseAction,
)


def create_execution_event(
    db: Session,
    run_id,
    agent_id,
    event_type: str,
    status: str,
    tool_name: str | None = None,
    details: dict | None = None,
) -> ExecutionEvent:

    event = ExecutionEvent(
        run_id=run_id,
        agent_id=agent_id,
        event_type=event_type,
        tool_name=tool_name,
        status=status,
        details=details or {},
    )

    db.add(event)
    db.flush()

    return event


def create_finding(
    db: Session,
    agent_id,
    run_id,
    tool_name: str,
    severity: str,
    reason: str,
    finding_type: str = "UNAUTHORIZED_TOOL",
    expected: str = "Tool must be allowed by behavior profile",
) -> Finding:

    finding = Finding(
        agent_id=agent_id,
        run_id=run_id,
        finding_type=finding_type,
        severity=severity,
        expected=expected,
        actual=tool_name,
        reason=reason,
        status="open",
    )

    db.add(finding)
    db.flush()

    return finding


def create_response_action(
    db: Session,
    finding_id,
    action_type: str,
    status: str,
    reason: str,
) -> ResponseAction:

    action = ResponseAction(
        finding_id=finding_id,
        action_type=action_type,
        status=status,
        reason=reason,
    )

    db.add(action)
    db.flush()

    return action


def create_approval(
    db: Session,
    finding_id,
    requested_by: str,
) -> Approval:

    approval = Approval(
        finding_id=finding_id,
        status="PENDING",
        requested_by=requested_by,
    )

    db.add(approval)
    db.flush()

    return approval


def create_audit_event(
    db: Session,
    agent_id,
    run_id,
    event_type: str,
    actor: str,
    finding_id=None,
    details: dict | None = None,
) -> AuditEvent:

    event = AuditEvent(
        agent_id=agent_id,
        run_id=run_id,
        finding_id=finding_id,
        event_type=event_type,
        actor=actor,
        details=details or {},
    )

    db.add(event)
    db.flush()

    return event
