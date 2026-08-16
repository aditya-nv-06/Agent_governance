import random
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
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

    for i in range(max(1, count)):
        run = AgentRun(agent_id=agent.id, input_message=f"Simulated question #{i+1}", status="completed")
        db.add(run)
        db.flush()

        # Record the initial LLM tool request
        db.add(ExecutionEvent(
            run_id=run.id,
            agent_id=agent.id,
            event_type="LLM_TOOL_REQUEST",
            tool_name=f"simulated_tool_{random.randint(1,3)}",
            status="requested",
            details={"message": run.input_message},
        ))

        # Randomly decide whether this run will be auto-executed or require approval
        if random.random() < 0.6:
            # auto execute
            db.add(ExecutionEvent(
                run_id=run.id,
                agent_id=agent.id,
                event_type="TOOL_EXECUTED",
                tool_name=f"simulated_tool_{random.randint(1,3)}",
                status="executed",
                details={"note": "auto-executed by simulation"},
            ))

            db.add(AuditEvent(
                agent_id=agent.id,
                run_id=run.id,
                finding_id=None,
                event_type="TOOL_EXECUTED",
                actor="simulator",
                details={"outcome": "auto"},
            ))

            results["auto_executed"] += 1

        else:
            # blocked -> create finding + approval
            finding = Finding(
                agent_id=agent.id,
                run_id=run.id,
                finding_type="policy_deviation",
                severity="HIGH",
                expected="No external action",
                actual="Requested external tool",
                reason="Simulated policy violation",
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

            db.add(ExecutionEvent(
                run_id=run.id,
                agent_id=agent.id,
                event_type="TOOL_BLOCKED",
                tool_name=f"simulated_tool_{random.randint(1,3)}",
                status="blocked",
                details={"reason": "requires human approval"},
            ))

            db.add(AuditEvent(
                agent_id=agent.id,
                run_id=run.id,
                finding_id=finding.id,
                event_type="APPROVAL_REQUESTED",
                actor="simulator",
                details={"note": "simulated approval requested"},
            ))

            results["approval_requested"] += 1

        run.completed_at = datetime.utcnow()
        db.commit()
        results["created_runs"] += 1

    return results


@router.get("/analytics/agents")
def agents_analytics(
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(require_admin),
):
    """Return simple analytics for agents owned by the admin."""

    agents = db.query(Agent).filter(Agent.owner_id == admin.id).all()

    out = []
    for agent in agents:
        runs_count = db.query(AgentRun).filter(AgentRun.agent_id == agent.id).count()

        approvals_count = (
            db.query(Approval)
            .join(Finding, Finding.id == Approval.finding_id)
            .filter(Finding.agent_id == agent.id)
            .count()
        )

        auto_executed = (
            db.query(ExecutionEvent)
            .filter(ExecutionEvent.agent_id == agent.id, ExecutionEvent.event_type == "TOOL_EXECUTED")
            .count()
        )

        blocked = (
            db.query(ExecutionEvent)
            .filter(ExecutionEvent.agent_id == agent.id, ExecutionEvent.event_type == "TOOL_BLOCKED")
            .count()
        )

        # average run duration (seconds)
        durations = []
        runs = db.query(AgentRun).filter(AgentRun.agent_id == agent.id).all()
        for r in runs:
            if r.completed_at and r.created_at:
                durations.append((r.completed_at - r.created_at).total_seconds())

        avg_duration = sum(durations) / len(durations) if durations else None

        out.append({
            "agent_id": str(agent.id),
            "agent_name": agent.name,
            "runs_count": runs_count,
            "approvals_count": approvals_count,
            "auto_executed": auto_executed,
            "blocked_count": blocked,
            "avg_run_seconds": avg_duration,
        })

    return out
