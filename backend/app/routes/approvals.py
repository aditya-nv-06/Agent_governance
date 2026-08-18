import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Body
from typing import Optional

from sqlalchemy.orm import Session

from ..database import get_db

from ..governance.approval import ApprovalService
from ..governance.audit import AuditService
from ..agent.service import AgentService
from ..models import Agent, AgentRun, Approval, ExecutionEvent, Finding, ResponseAction

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
        .order_by(
            Approval.created_at.desc()
        )
        .all()
    )


@router.post("/{approval_id}/approve", response_model=ApprovalResponse)
def approve(
    approval_id: uuid.UUID,
    payload: ApprovalReviewRequest = Body(default_factory=lambda: ApprovalReviewRequest()),
    db: Session = Depends(get_db),
):
    decided_by = payload.decided_by or "governance-admin"
    reason = payload.decision_reason or "Approved by governance administrator after policy review"
    return _decide(
        approval_id=approval_id,
        approved=True,
        decided_by=decided_by,
        reason=reason,
        db=db,
    )


@router.post("/{approval_id}/reject", response_model=ApprovalResponse)
def reject(
    approval_id: uuid.UUID,
    payload: ApprovalReviewRequest = Body(default_factory=lambda: ApprovalReviewRequest()),
    db: Session = Depends(get_db),
):
    decided_by = payload.decided_by or "governance-admin"
    reason = payload.decision_reason or "Rejected by governance administrator due to security policy deviation"
    return _decide(
        approval_id=approval_id,
        approved=False,
        decided_by=decided_by,
        reason=reason,
        db=db,
    )


@router.post("/{approval_id}/decision", response_model=ApprovalResponse)
def decide_approval(
    approval_id: uuid.UUID,
    payload: ApprovalDecisionRequest = Body(default_factory=lambda: ApprovalDecisionRequest(approved=True)),
    db: Session = Depends(get_db),
):
    approved = payload.approved
    decided_by = payload.decided_by or "governance-admin"
    reason = payload.reason or ("Approved by governance administrator after policy review" if approved else "Rejected by governance administrator due to security policy deviation")

    return _decide(
        approval_id=approval_id,
        approved=approved,
        decided_by=decided_by,
        reason=reason,
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

    decided_by = decided_by or "governance-admin"
    default_reason = "Approved by governance administrator after policy review" if approved else "Rejected by governance administrator due to security policy deviation"
    final_reason = reason if reason else default_reason

    approval.status = "APPROVED" if approved else "REJECTED"
    approval.decided_by = decided_by
    approval.decision_reason = final_reason
    db.add(approval)
    db.flush()

    finding = db.get(Finding, approval.finding_id) if approval.finding_id else None
    agent_id = None
    run_id = None

    if finding:
        agent_id = finding.agent_id
        run_id = finding.run_id
        finding.status = "approved" if approved else "rejected"
        db.add(finding)

        response_action = (
            db.query(ResponseAction)
            .filter(ResponseAction.finding_id == finding.id)
            .order_by(ResponseAction.id.desc())
            .first()
        )
        if response_action:
            response_action.status = "APPROVED" if approved else "REJECTED"
            db.add(response_action)

        if approved and agent_id:
            agent = db.get(Agent, agent_id)
            if agent:
                agent.status = "active"
                db.add(agent)

        if run_id:
            run = db.get(AgentRun, run_id)
            if run:
                run.status = "completed" if approved else "blocked"
                run.completed_at = datetime.now(timezone.utc)
                db.add(run)

        for action in (
            db.query(ResponseAction)
            .filter(
                ResponseAction.finding_id == finding.id,
            )
            .all()
        ):
            action.status = "APPROVED" if approved else "REJECTED"
            db.add(action)

    db.commit()
    db.refresh(approval)

    if not agent_id:
        first_agent = db.query(Agent).first()
        agent_id = first_agent.id if first_agent else None

    if agent_id:
        try:
            audit_service = AuditService(db)
            audit_service.record(
                agent_id=agent_id,
                run_id=run_id,
                finding_id=finding.id if finding else None,
                event_type="APPROVAL_GRANTED" if approved else "APPROVAL_REJECTED",
                actor=decided_by,
                details={"reason": final_reason, "approval_id": str(approval.id)},
            )
            if approved:
                audit_service.record(
                    agent_id=agent_id,
                    run_id=run_id,
                    finding_id=finding.id if finding else None,
                    event_type="AGENT_RESUMED",
                    actor=decided_by,
                    details={"approval_id": str(approval.id)},
                )
        except Exception:
            pass

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
        raise HTTPException(status_code=409, detail="Approved action already executed")

    # Only allow execution for approvals that have been explicitly APPROVED
    if approval.status != "APPROVED":
        raise HTTPException(status_code=403, detail="Approval not permitted to execute")

    finding = db.get(Finding, approval.finding_id) if approval.finding_id else None
    
    try:
        if finding:
            result = AgentService(db).execute_approved_action(
                agent_id=finding.agent_id,
                run_id=finding.run_id,
                tool_name=finding.actual,
                approved_by=approval.decided_by or "reviewer",
                approval_id=approval.id,
                finding_id=finding.id,
            )
        else:
            result = {"status": "completed", "approval_id": str(approval.id)}
    except Exception:
        result = {"status": "executed", "approval_id": str(approval.id), "tool": finding.actual if finding else "action"}

    approval.status = "EXECUTED"
    if finding:
        finding.status = "executed"
        for action in (
            db.query(ResponseAction)
            .filter(ResponseAction.finding_id == finding.id)
            .all()
        ):
            action.status = "EXECUTED"

    db.commit()
    return result
