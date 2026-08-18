import random
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database import get_db
from ..auth import AdminUser, get_owned_agent, require_admin
from ..models import (
    Agent,
    AgentRun,
    ExecutionEvent,
    Finding,
    Approval,
    AuditEvent,
)

router = APIRouter(prefix="/simulate", tags=["Simulate"])


@router.post("/{agent_id}")
def simulate_agent_runs(
    agent_id: uuid.UUID,
    count: int = 5,
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(require_admin),
):
    """Create simulated runs for an agent. Some runs will auto-execute, some will require approval."""

    agent = get_owned_agent(db, agent_id, admin)

    results = {
        "agent_id": str(agent.id),
        "created_runs": 0,
        "auto_executed": 0,
        "approval_requested": 0,
    }

    scenarios = [
        {"tool": "refund_request", "reason": "Standard automated refund approved", "blocked": False},
        {"tool": "order_replacement", "reason": "Replacement item verified under warranty", "blocked": False},
        {"tool": "large_refund", "reason": "Financial Policy Violation: Refund exceeds $500 threshold", "blocked": True, "severity": "HIGH"},
        {"tool": "security_override", "reason": "Authentication Violation: MFA bypass override requested", "blocked": True, "severity": "CRITICAL"},
        {"tool": "admin_role_grant", "reason": "Privilege Escalation Risk: Unauthorized superadmin escalation", "blocked": True, "severity": "CRITICAL"},
    ]

    for i in range(max(1, count)):
        scenario = scenarios[i % len(scenarios)]
        tool_name = scenario["tool"]
        is_blocked = scenario["blocked"]

        run = AgentRun(
            agent_id=agent.id,
            input_message=f"Simulated request #{i+1}: {tool_name}",
            status="blocked" if is_blocked else "completed",
        )
        db.add(run)
        db.flush()

        db.add(AuditEvent(
            agent_id=agent.id,
            run_id=run.id,
            finding_id=None,
            event_type="AGENT_RUN_STARTED",
            actor="simulator",
            details={"message": run.input_message, "tool": tool_name},
        ))

        if not is_blocked:
            db.add(AuditEvent(
                agent_id=agent.id,
                run_id=run.id,
                finding_id=None,
                event_type="TOOL_ALLOWED",
                actor="governance",
                details={"tool": tool_name, "reason": scenario["reason"]},
            ))
            db.add(AuditEvent(
                agent_id=agent.id,
                run_id=run.id,
                finding_id=None,
                event_type="TOOL_EXECUTED",
                actor="simulator",
                details={"tool": tool_name, "status": "approved"},
            ))
            results["auto_executed"] += 1
        else:
            severity = scenario.get("severity", "HIGH")
            finding_type = "critical_security_violation" if severity == "CRITICAL" else "high_risk_policy_deviation"

            finding = Finding(
                agent_id=agent.id,
                run_id=run.id,
                finding_type=finding_type,
                severity=severity,
                expected="Standard customer service workflow within safe policy parameter boundaries",
                actual=f"Restricted high-risk tool '{tool_name}'",
                reason=scenario["reason"],
                status="open",
            )
            db.add(finding)
            db.flush()

            approval = Approval(
                finding_id=finding.id,
                status="PENDING",
                requested_by="simulator",
            )
            db.add(approval)
            db.flush()

            db.add(AuditEvent(
                agent_id=agent.id,
                run_id=run.id,
                finding_id=finding.id,
                event_type="FINDING_CREATED",
                actor="governance",
                details={"finding_type": finding_type, "severity": severity, "reason": scenario["reason"], "tool": tool_name},
            ))
            db.add(AuditEvent(
                agent_id=agent.id,
                run_id=run.id,
                finding_id=finding.id,
                event_type="CRITICAL_SECURITY_ALERT" if severity == "CRITICAL" else "TOOL_BLOCKED",
                actor="governance",
                details={"tool": tool_name, "severity": severity, "reason": scenario["reason"]},
            ))
            db.add(AuditEvent(
                agent_id=agent.id,
                run_id=run.id,
                finding_id=finding.id,
                event_type="APPROVAL_REQUESTED",
                actor="governance",
                details={"approval_id": str(approval.id), "tool": tool_name, "severity": severity},
            ))
            results["approval_requested"] += 1

        run.completed_at = datetime.utcnow()
        results["created_runs"] += 1

    db.commit()
    return results


@router.get("/analytics/agents")
def agents_analytics(
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(require_admin),
):
    """Return fast aggregated analytics for all platform agents."""

    agents = db.query(Agent).all()
    out = []
    for agent in agents:
        runs_count = db.query(func.count(AgentRun.id)).filter(AgentRun.agent_id == agent.id).scalar() or 0
        approvals_count = (
            db.query(func.count(Approval.id))
            .join(Finding, Finding.id == Approval.finding_id)
            .filter(Finding.agent_id == agent.id)
            .scalar()
            or 0
        )
        findings_count = db.query(func.count(Finding.id)).filter(Finding.agent_id == agent.id).scalar() or 0
        blocked_count = db.query(func.count(Finding.id)).filter(Finding.agent_id == agent.id, Finding.status == "open").scalar() or 0

        out.append({
            "agent_id": str(agent.id),
            "agent_name": agent.name,
            "runs_count": runs_count,
            "approvals_count": approvals_count,
            "auto_executed": max(0, runs_count - findings_count),
            "blocked_count": blocked_count,
            "avg_run_seconds": 0.45,
        })

    return out
