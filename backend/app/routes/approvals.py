import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException

from sqlalchemy.orm import Session

from ..database import get_db

from ..governance.approval import ApprovalService
from ..governance.audit import AuditService
from ..agent.service import AgentService
from ..models import Agent, Approval, ExecutionEvent, Finding, ResponseAction

from ..schemas import (
    ApprovalDecisionRequest,
    ApprovalResponse,
    ApprovalReviewRequest,
)


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
        .filter(Approval.status.in_(["PENDING", "APPROVED"]))
        .order_by(
            Approval.created_at.desc()
        )
        .all()
    )


@router.post("/{approval_id}/approve", response_model=ApprovalResponse)
def approve(
    approval_id: uuid.UUID,
    payload: ApprovalReviewRequest,
    db: Session = Depends(get_db),
):
    return _decide(
        approval_id=approval_id,
        approved=True,
        decided_by=payload.decided_by,
        reason=payload.decision_reason,
        db=db,
    )


@router.post("/{approval_id}/reject", response_model=ApprovalResponse)
def reject(
    approval_id: uuid.UUID,
    payload: ApprovalReviewRequest,
    db: Session = Depends(get_db),
):
    return _decide(
        approval_id=approval_id,
        approved=False,
        decided_by=payload.decided_by,
        reason=payload.decision_reason,
        db=db,
    )


@router.post("/{approval_id}/decision", response_model=ApprovalResponse)
def decide_approval(
    approval_id: uuid.UUID,
    payload: ApprovalDecisionRequest,
    db: Session = Depends(get_db),
):
    return _decide(
        approval_id=approval_id,
        approved=payload.approved,
        decided_by=payload.decided_by,
        reason=payload.reason,
        db=db,
    )


def _decide(
    approval_id: uuid.UUID,
    approved: bool,
    decided_by: str,
    reason: str,
    db: Session,
):
    approval = db.get(Approval, approval_id)
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
    if approval.status != "PENDING":
        raise HTTPException(status_code=409, detail="Approval has already been decided")

    approval = ApprovalService(db).decide(approval_id, approved, decided_by, reason)
    finding = db.get(Finding, approval.finding_id)
    if finding:
        finding.status = "approved" if payload.approved else "rejected"
        response_action = (
            db.query(ResponseAction)
            .filter(ResponseAction.finding_id == finding.id)
            .order_by(ResponseAction.id.desc())
            .first()
        )
        if response_action:
            response_action.status = "APPROVED" if payload.approved else "REJECTED"
        agent = db.get(Agent, finding.agent_id)
        if agent and approved:
            agent.status = "active"
        run = db.get(AgentRun, finding.run_id)
        if not approved:
            if run:
                run.status = "blocked"
                run.completed_at = datetime.now(timezone.utc)
            for action in (
                db.query(ResponseAction)
                .filter(
                    ResponseAction.finding_id == finding.id,
                    ResponseAction.status == "PENDING",
                )
                .all()
            ):
                action.status = "REJECTED"
        db.commit()
        AuditService(db).record(
            agent_id=finding.agent_id,
            run_id=finding.run_id,
            finding_id=finding.id,
            event_type="APPROVAL_GRANTED" if approved else "APPROVAL_REJECTED",
            actor=decided_by,
            details={"reason": reason, "approval_id": str(approval.id)},
        )
        if approved:
            AuditService(db).record(
                agent_id=finding.agent_id,
                run_id=finding.run_id,
                finding_id=finding.id,
                event_type="AGENT_RESUMED",
                actor=decided_by,
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
    if approval.status == "EXECUTED":
        raise HTTPException(status_code=409, detail="Approved action has already executed")
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
            ExecutionEvent.event_type == "APPROVED_TOOL_EXECUTION",
        )
        .first()
    )
    if already_executed:
        raise HTTPException(status_code=409, detail="Approved action has already executed")

    try:
        result = AgentService(db).execute_approved_action(
            agent_id=finding.agent_id,
            run_id=finding.run_id,
            tool_name=finding.actual,
            approved_by=approval.decided_by or "reviewer",
            approval_id=approval.id,
            finding_id=finding.id,
        )
        approval.status = "EXECUTED"
        finding.status = "executed"
        response_action = (
            db.query(ResponseAction)
            .filter(ResponseAction.finding_id == finding.id)
            .order_by(ResponseAction.id.desc())
            .first()
        )
        if response_action:
            response_action.status = "EXECUTED"
        db.commit()
        return result
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
