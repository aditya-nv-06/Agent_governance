import uuid

from fastapi import APIRouter, Depends, HTTPException

from sqlalchemy.orm import Session

from ..database import get_db

from ..governance.approval import ApprovalService
from ..governance.audit import AuditService
from ..agent.service import AgentService
from ..models import Agent, Approval, ExecutionEvent, Finding

from ..schemas import ApprovalDecisionRequest, ApprovalResponse


router = APIRouter(
    prefix="/approvals",
    tags=["Approvals"],
)


@router.get(
    "",
    response_model=list[ApprovalResponse],
)
def get_approvals(
    db: Session = Depends(get_db),
):

    return (
        db.query(Approval)
        .order_by(
            Approval.created_at.desc()
        )
        .all()
    )


@router.post("/{approval_id}/decision", response_model=ApprovalResponse)
def decide_approval(
    approval_id: uuid.UUID,
    payload: ApprovalDecisionRequest,
    db: Session = Depends(get_db),
):
    approval = db.get(Approval, approval_id)
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
    if approval.status != "PENDING":
        raise HTTPException(status_code=409, detail="Approval has already been decided")

    approval = ApprovalService(db).decide(
        approval_id, payload.approved, payload.decided_by, payload.reason
    )
    finding = db.get(Finding, approval.finding_id)
    if finding:
        finding.status = "resolved" if payload.approved else "blocked"
        agent = db.get(Agent, finding.agent_id)
        if agent and payload.approved:
            agent.status = "active"
        db.commit()
        AuditService(db).record(
            agent_id=finding.agent_id,
            run_id=finding.run_id,
            finding_id=finding.id,
            event_type="APPROVAL_GRANTED" if payload.approved else "APPROVAL_REJECTED",
            actor=payload.decided_by,
            details={"reason": payload.reason, "approval_id": str(approval.id)},
        )
        if payload.approved:
            AuditService(db).record(
                agent_id=finding.agent_id,
                run_id=finding.run_id,
                finding_id=finding.id,
                event_type="AGENT_RESUMED",
                actor=payload.decided_by,
                details={"approval_id": str(approval.id)},
            )
    return approval


@router.post("/{approval_id}/execute")
def execute_approved_action(
    approval_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    approval = db.get(Approval, approval_id)
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
    if approval.status != "APPROVED":
        raise HTTPException(
            status_code=403,
            detail="Only an approved action can be executed",
        )

    finding = db.get(Finding, approval.finding_id)
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")
    already_executed = (
        db.query(ExecutionEvent)
        .filter(
            ExecutionEvent.run_id == finding.run_id,
            ExecutionEvent.event_type == "APPROVED_TOOL_EXECUTED",
        )
        .first()
    )
    if already_executed:
        raise HTTPException(status_code=409, detail="Approved action has already executed")

    try:
        return AgentService(db).execute_approved_action(
            agent_id=finding.agent_id,
            run_id=finding.run_id,
            tool_name=finding.actual,
            approved_by=approval.decided_by or "reviewer",
            approval_id=approval.id,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
