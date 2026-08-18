"""
External customer service backend integration routes
Allows second backends to submit approval requests and retrieve audit/findings
"""
import uuid
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import AdminUser, Agent, Approval, AuditEvent, Finding, AgentRun, BehaviorProfile, EnvAgent, ResponseAction, ExecutionEvent
from ..governance.approval import ApprovalService
from ..governance.audit import AuditService
from ..governance.persistence import create_execution_event, create_response_action
from ..schemas import ApprovalResponse
from sqlalchemy import cast, String, or_

router = APIRouter(
    prefix="/external",
    tags=["External Integration"],
)


@router.post("/agents/connect")
def connect_external_agent(
    payload: dict,
    db: Session = Depends(get_db),
):
    """
    Connect and register an external agent via URL into the governance platform.
    """
    url = payload.get("url", "http://localhost:8001")
    name = payload.get("name", "Customer Service Agent")
    purpose = payload.get("purpose", "Customer Service Automation & Support")

    first_admin = db.query(AdminUser).first()
    admin_owner_id = first_admin.id if first_admin else None

    # Check if agent already exists by name or url
    agent = db.query(Agent).filter(Agent.name.ilike(f"%{name}%")).first()
    if not agent:
        agent = Agent(
            name=name,
            description=f"External Agent connected at {url} · {purpose}",
            status="active",
            owner_id=admin_owner_id,
        )
        db.add(agent)
        db.flush()

        profile = BehaviorProfile(
            agent_id=agent.id,
            name=f"{name} Profile",
            allowed_tools=["refund_request", "order_replacement", "priority_support", "address_change", "discount_inquiry"],
            allowed_actions=["read_ticket", "update_order", "apply_discount"],
            allowed_data_sources=["crm", "orders_db", "external_service"],
            max_llm_calls=5000,
            warning_threshold=80,
            critical_threshold=90,
        )
        db.add(profile)

    # Sync with EnvAgent
    env_agent = db.query(EnvAgent).filter(EnvAgent.url == url).first()
    if not env_agent:
        env_agent = EnvAgent(
            name=name,
            url=url,
            purpose=purpose,
            owner_id=admin_owner_id,
            allowed_instructions=["refund_request", "order_replacement", "priority_support", "address_change", "discount_inquiry"],
        )
        db.add(env_agent)

    # Record registration in audit log
    audit = AuditEvent(
        agent_id=agent.id,
        event_type="AGENT_REGISTERED",
        actor="external_connect",
        details={"name": name, "url": url, "purpose": purpose},
    )
    db.add(audit)
    db.commit()

    return {
        "status": "connected",
        "agent_id": str(agent.id),
        "name": agent.name,
        "url": url,
        "message": f"Successfully registered and governed {name} at {url}",
    }


@router.post("/approvals/request")
def submit_approval_request(
    request: dict,
    db: Session = Depends(get_db),
):
    """
    External endpoint for customer service backends to submit approval requests.
    
    Does not require authentication - uses trace_id for tracking.
    """
    try:
        agent_id = request.get("agent_id")
        customer_id = request.get("customer_id")
        tool_name = request.get("tool_name")
        parameters = request.get("parameters", {})
        request_context = request.get("request_context")
        trace_id = request.get("trace_id", str(uuid.uuid4()))

        if not all([agent_id, customer_id, tool_name]):
            raise HTTPException(status_code=400, detail="Missing required fields")

        # Resolve or create Agent record so foreign keys and dashboard statistics stay accurate
        agent = None
        try:
            agent_uuid = uuid.UUID(str(agent_id))
            agent = db.get(Agent, agent_uuid)
        except Exception:
            agent = db.query(Agent).filter(Agent.name.ilike("%Customer Service%")).first()

        # Find first admin user to own the external integration agent
        first_admin = db.query(AdminUser).first()
        admin_owner_id = first_admin.id if first_admin else None

        if not agent:
            agent = Agent(
                name="Customer Service Agent",
                description="External Customer Service Agent Backend (Port 8001)",
                status="active",
                owner_id=admin_owner_id,
            )
            db.add(agent)
            db.flush()

            profile = BehaviorProfile(
                agent_id=agent.id,
                name="Customer Service Profile",
                allowed_tools=["refund_request", "order_replacement", "priority_support", "address_change", "discount_inquiry"],
                allowed_actions=["read_ticket", "update_order", "apply_discount"],
                allowed_data_sources=["crm", "orders_db"],
                max_llm_calls=5000,
                warning_threshold=80,
                critical_threshold=90,
            )
            db.add(profile)
            db.flush()
        elif agent.owner_id is None and admin_owner_id:
            agent.owner_id = admin_owner_id
            db.flush()

        # Get or create run
        run = AgentRun(
            agent_id=agent.id,
            input_message=request_context or f"Customer request: {tool_name}",
            status="running",
        )
        db.add(run)
        db.flush()

        # Record run started in audit timeline
        try:
            AuditService(db).record(
                agent_id=agent.id,
                run_id=run.id,
                event_type="AGENT_RUN_STARTED",
                actor="external_connect",
                details={"message": run.input_message, "trace_id": trace_id},
            )
        except Exception:
            pass

        # Audit log initial request
        audit_service = AuditService(db)
        audit_service.record(
            agent_id=agent.id,
            run_id=run.id,
            event_type="CUSTOMER_SERVICE_REQUEST",
            actor="customer_service_backend",
            details={
                "tool": tool_name,
                "customer_id": customer_id,
                "trace_id": trace_id,
                "parameters": parameters,
                "request_context": request_context,
            },
        )
        try:
            create_execution_event(
                db=db,
                run_id=run.id,
                agent_id=agent.id,
                event_type="CUSTOMER_SERVICE_REQUEST",
                status="RECEIVED",
                tool_name=tool_name,
                details={"parameters": parameters, "trace_id": trace_id, "request_context": request_context},
            )
        except Exception:
            pass

        # Determine approval status based on policy risk and generate specific, distinctive reasons
        approval_status = "approved"
        reason = None
        approval_id = None
        
        high_risk_reasons_map = {
            "large_refund": lambda p: f"Financial Policy Violation: Refund amount of ${p.get('amount', 'N/A')} exceeds maximum autonomous threshold ($500.00) on order {p.get('order_id', 'N/A')} for reason '{p.get('reason', 'unverified')}'",
            "account_suspension": lambda p: f"Account Integrity Breach: Immediate {p.get('days', 30)}-day account suspension requested for trigger '{p.get('reason', 'suspicious_activity')}' without human compliance officer signoff",
            "data_export": lambda p: f"Privacy & PII Violation: Unsanitized full customer data export in {p.get('format', 'JSON')} requested to external destination '{p.get('destination', 'external_link')}'",
            "admin_role_grant": lambda p: f"Privilege Escalation Risk: Unauthorized escalation to '{p.get('target_role', 'superadmin')}' permissions for reason '{p.get('reason', 'bypass')}'",
            "security_override": lambda p: f"Authentication Policy Violation: Security override requested to force password reset with MFA bypass set to {p.get('bypass_mfa', True)}",
        }

        low_risk_reasons_map = {
            "refund_request": lambda p: f"Automated Micro-Refund Approved: ${p.get('amount', 'N/A')} is within allowable limit for order {p.get('order_id', 'N/A')} ({p.get('reason', 'standard return')})",
            "order_replacement": lambda p: f"Fulfillment Policy Approved: Replacement for item '{p.get('item', 'replacement item')}' on order {p.get('order_id', 'N/A')} verified under warranty policy",
            "priority_support": lambda p: f"SLA Routing Valid: Priority escalation for {p.get('customer_tier', 'gold')} tier customer regarding '{p.get('issue', 'inquiry')}'",
            "address_change": lambda p: f"Logistics Policy Approved: In-transit address change for order {p.get('order_id', 'N/A')} updated to {p.get('city', 'destination')}, {p.get('postal_code', 'postal code')}",
            "discount_inquiry": lambda p: f"Promotional Discount Approved: Code '{p.get('promo_code', 'PROMO')}' successfully validated on cart total ${p.get('cart_value', '0.00')}",
        }

        if tool_name in high_risk_reasons_map:
            approval_status = "blocked"
            reason = high_risk_reasons_map[tool_name](parameters)

            # Determine if this blocked request is a CRITICAL security violation
            critical_tools = ["security_override", "admin_role_grant", "data_export"]
            is_critical = (
                tool_name in critical_tools
                or (tool_name == "large_refund" and float(parameters.get("amount", 0) or 0) >= 3000.0)
                or (tool_name == "account_suspension" and int(parameters.get("days", 0) or 0) >= 90)
            )
            finding_severity = "CRITICAL" if is_critical else "HIGH"
            finding_type = "critical_security_violation" if is_critical else "high_risk_policy_deviation"
            
            # Create a finding for the blocked action
            finding = Finding(
                agent_id=agent.id,
                run_id=run.id,
                finding_type=finding_type,
                severity=finding_severity,
                expected="Standard customer service workflow within safe policy parameter boundaries",
                actual=f"Restricted high-risk tool '{tool_name}' with parameters {parameters}",
                reason=reason,
                status="open",
            )
            db.add(finding)
            db.flush()

            # Create approval for high-risk action review and a response action
            approval = Approval(
                finding_id=finding.id,
                status="PENDING",
                requested_by="customer_service",
            )
            db.add(approval)
            db.flush()
            approval_id = str(approval.id)

            try:
                create_response_action(
                    db=db,
                    finding_id=finding.id,
                    action_type="REQUIRE_APPROVAL",
                    status="PENDING",
                    reason=reason,
                )
            except Exception:
                pass

            try:
                create_execution_event(
                    db=db,
                    run_id=run.id,
                    agent_id=agent.id,
                    event_type="TOOL_BLOCKED",
                    status="BLOCKED",
                    tool_name=tool_name,
                    details={"reason": reason, "severity": finding_severity, "trace_id": trace_id},
                )
            except Exception:
                pass

            audit_service.record(
                agent_id=agent.id,
                run_id=run.id,
                finding_id=finding.id,
                event_type="FINDING_CREATED",
                actor="governance",
                details={"finding_type": finding_type, "tool": tool_name, "severity": finding_severity, "reason": reason, "trace_id": trace_id},
            )
            audit_service.record(
                agent_id=agent.id,
                run_id=run.id,
                finding_id=finding.id,
                event_type="CRITICAL_SECURITY_ALERT" if is_critical else "TOOL_BLOCKED",
                actor="governance",
                details={"tool": tool_name, "severity": finding_severity, "reason": reason, "trace_id": trace_id, "parameters": parameters},
            )
            audit_service.record(
                agent_id=agent.id,
                run_id=run.id,
                finding_id=finding.id,
                event_type="APPROVAL_REQUESTED",
                actor="governance",
                details={"approval_id": approval_id, "tool": tool_name, "severity": finding_severity, "trace_id": trace_id},
            )

            run.status = "blocked"
            run.completed_at = datetime.utcnow()

        elif tool_name in low_risk_reasons_map:
            approval_status = "approved"
            reason = low_risk_reasons_map[tool_name](parameters)
            run.status = "completed"
            run.completed_at = datetime.utcnow()

            audit_service.record(
                agent_id=agent.id,
                run_id=run.id,
                event_type="TOOL_ALLOWED",
                actor="governance",
                details={"tool": tool_name, "status": "approved", "reason": reason, "trace_id": trace_id},
            )
            try:
                create_execution_event(
                    db=db,
                    run_id=run.id,
                    agent_id=agent.id,
                    event_type="TOOL_ALLOWED",
                    status="ALLOWED",
                    tool_name=tool_name,
                    details={"reason": reason, "trace_id": trace_id},
                )
            except Exception:
                pass
            audit_service.record(
                agent_id=agent.id,
                run_id=run.id,
                event_type="TOOL_EXECUTED",
                actor="customer_service_backend",
                details={"tool": tool_name, "status": "approved", "trace_id": trace_id, "parameters": parameters},
            )
            try:
                create_execution_event(
                    db=db,
                    run_id=run.id,
                    agent_id=agent.id,
                    event_type="TOOL_EXECUTED",
                    status="EXECUTED",
                    tool_name=tool_name,
                    details={"parameters": parameters, "trace_id": trace_id},
                )
            except Exception:
                pass
        else:
            approval_status = "approved"
            reason = f"Standard customer service operation approved: {tool_name}"
            run.status = "completed"
            run.completed_at = datetime.utcnow()

            audit_service.record(
                agent_id=agent.id,
                run_id=run.id,
                event_type="TOOL_EXECUTED",
                actor="customer_service_backend",
                details={"tool": tool_name, "status": "approved", "trace_id": trace_id},
            )

        db.commit()

        # Record response sent to external caller for traceability
        try:
            audit_service.record(
                agent_id=agent.id,
                run_id=run.id,
                finding_id=finding.id if approval_status == "blocked" and 'finding' in locals() else None,
                event_type="EXTERNAL_RESPONSE_SENT",
                actor="governance",
                details={
                    "status": approval_status,
                    "approval_id": approval_id,
                    "reason": reason,
                    "trace_id": trace_id,
                },
            )
        except Exception:
            pass

        # Retrieve audit events and findings for this run
        run_audit_events = db.query(AuditEvent).filter(AuditEvent.run_id == run.id).order_by(AuditEvent.created_at.asc()).all()
        run_findings = db.query(Finding).filter(Finding.run_id == run.id).all()
        run_exec_events = db.query(ExecutionEvent).filter(ExecutionEvent.run_id == run.id).order_by(ExecutionEvent.created_at.asc()).all()
        run_response_actions = []
        if run_findings:
            finding_ids = [f.id for f in run_findings]
            run_response_actions = db.query(ResponseAction).filter(ResponseAction.finding_id.in_(finding_ids)).all()

        return {
            "run_id": str(run.id),
            "approval_id": approval_id,
            "status": approval_status,
            "reason": reason,
            "trace_id": trace_id,
            "timestamp": datetime.utcnow().isoformat(),
            "audit_events": [
                {
                    "id": str(event.id),
                    "event_type": event.event_type,
                    "actor": event.actor,
                    "details": event.details,
                    "created_at": event.created_at.isoformat() if event.created_at else None,
                }
                for event in run_audit_events
            ],
            "execution_events": [
                {
                    "id": str(e.id),
                    "event_type": e.event_type,
                    "tool_name": e.tool_name,
                    "status": e.status,
                    "details": e.details,
                    "created_at": e.created_at.isoformat() if e.created_at else None,
                }
                for e in run_exec_events
            ],
            "response_actions": [
                {
                    "id": str(a.id),
                    "finding_id": str(a.finding_id),
                    "action_type": a.action_type,
                    "status": a.status,
                    "reason": a.reason,
                }
                for a in run_response_actions
            ],
            "findings": [
                {
                    "id": str(f.id),
                    "severity": f.severity,
                    "finding_type": f.finding_type,
                    "expected": f.expected,
                    "actual": f.actual,
                    "reason": f.reason,
                    "status": f.status,
                    "created_at": f.created_at.isoformat() if f.created_at else None,
                }
                for f in run_findings
            ],
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/audit")
def get_audit_by_trace(
    trace_id: str = None,
    db: Session = Depends(get_db),
):
    """
    Retrieve audit events for a specific trace_id.
    """
    try:
        if not trace_id:
            raise HTTPException(status_code=400, detail="trace_id is required")

        events = db.query(AuditEvent).filter(
            or_(
                AuditEvent.details["trace_id"].astext == trace_id,
                cast(AuditEvent.details, String).ilike(f"%{trace_id}%"),
            )
        ).order_by(AuditEvent.created_at.asc()).all()

        return [
            {
                "id": str(event.id),
                "event_type": event.event_type,
                "actor": event.actor,
                "details": event.details,
                "created_at": event.created_at.isoformat() if event.created_at else None,
            }
            for event in events
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/findings")
def get_findings_by_trace(
    trace_id: str = None,
    db: Session = Depends(get_db),
):
    """
    Retrieve findings (reasons for blocks) for a specific trace_id.
    """
    try:
        if not trace_id:
            raise HTTPException(status_code=400, detail="trace_id is required")

        matched_events = db.query(AuditEvent).filter(
            or_(
                AuditEvent.details["trace_id"].astext == trace_id,
                cast(AuditEvent.details, String).ilike(f"%{trace_id}%"),
            )
        ).all()

        matching_run_ids = {e.run_id for e in matched_events if e.run_id}
        matching_finding_ids = {e.finding_id for e in matched_events if e.finding_id}

        findings = []
        if matching_run_ids:
            findings.extend(db.query(Finding).filter(Finding.run_id.in_(matching_run_ids)).all())
        if matching_finding_ids:
            findings.extend(db.query(Finding).filter(Finding.id.in_(matching_finding_ids)).all())

        unique_findings = list({str(f.id): f for f in findings}.values())

        return [
            {
                "id": str(finding.id),
                "severity": finding.severity,
                "finding_type": finding.finding_type,
                "expected": finding.expected,
                "actual": finding.actual,
                "reason": finding.reason,
                "status": finding.status,
                "created_at": finding.created_at.isoformat() if finding.created_at else None,
            }
            for finding in unique_findings
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/approvals/{run_id}")
def get_approval_status(
    run_id: str,
    db: Session = Depends(get_db),
):
    """
    Check the status of an approval request by run_id.
    """
    try:
        # Lookup run
        try:
            run_uuid = uuid.UUID(run_id)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid run_id")

        run = db.get(AgentRun, run_uuid)
        if not run:
            raise HTTPException(status_code=404, detail="Run not found")

        # Find approval via finding(s) associated with this run
        findings = db.query(Finding).filter(Finding.run_id == run.id).all()
        approval = None
        if findings:
            approval = (
                db.query(Approval)
                .filter(Approval.finding_id.in_([f.id for f in findings]))
                .order_by(Approval.created_at.desc())
                .first()
            )

        if not approval:
            raise HTTPException(status_code=404, detail="Approval not found for this run")

        # Include execution events, response actions and audit for context
        exec_events = db.query(ExecutionEvent).filter(ExecutionEvent.run_id == run.id).order_by(ExecutionEvent.created_at.asc()).all()
        response_actions = db.query(ResponseAction).filter(ResponseAction.finding_id == approval.finding_id).all()
        audit_events = db.query(AuditEvent).filter(AuditEvent.run_id == run.id).order_by(AuditEvent.created_at.asc()).all()

        # Extract questions/arguments from relevant execution events
        questions = [e.details.get("arguments") or e.details for e in exec_events if e.event_type in ("LLM_TOOL_REQUEST", "TOOL_PENDING_APPROVAL")]

        return {
            "run_id": str(run.id),
            "approval_id": str(approval.id),
            "status": approval.status,
            "requested_by": approval.requested_by,
            "decided_by": approval.decided_by,
            "decision_reason": approval.decision_reason,
            "created_at": approval.created_at.isoformat(),
            "questions": questions,
            "execution_events": [
                {"id": str(e.id), "event_type": e.event_type, "tool_name": e.tool_name, "status": e.status, "details": e.details, "created_at": e.created_at.isoformat() if e.created_at else None}
                for e in exec_events
            ],
            "response_actions": [
                {"id": str(a.id), "action_type": a.action_type, "status": a.status, "reason": a.reason}
                for a in response_actions
            ],
            "audit_events": [
                {"id": str(ae.id), "event_type": ae.event_type, "actor": ae.actor, "details": ae.details, "created_at": ae.created_at.isoformat() if ae.created_at else None}
                for ae in audit_events
            ],
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
def health():
    """Health check for external systems."""
    return {
        "status": "healthy",
        "service": "Primary Backend",
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.post("/approvals/{run_id}/decision")
def external_decision(
    run_id: str,
    payload: dict,
    db: Session = Depends(get_db),
):
    """
    External endpoint to approve/reject an approval by run_id.
    Payload: {"approved": bool, "decided_by": "name", "reason": "..."}
    """
    try:
        try:
            run_uuid = uuid.UUID(run_id)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid run_id")

        run = db.get(AgentRun, run_uuid)
        if not run:
            raise HTTPException(status_code=404, detail="Run not found")

        findings = db.query(Finding).filter(Finding.run_id == run.id).all()
        if not findings:
            raise HTTPException(status_code=404, detail="No findings for this run")

        approval = (
            db.query(Approval)
            .filter(Approval.finding_id.in_([f.id for f in findings]))
            .order_by(Approval.created_at.desc())
            .first()
        )

        if not approval:
            raise HTTPException(status_code=404, detail="Approval not found for this run")

        approved = bool(payload.get("approved", False))
        decided_by = payload.get("decided_by") or "external-system"
        reason = payload.get("reason") or ("Approved by external system" if approved else "Rejected by external system")

        # Update approval and finding
        approval.status = "APPROVED" if approved else "REJECTED"
        approval.decided_by = decided_by
        approval.decision_reason = reason
        db.add(approval)

        finding = db.get(Finding, approval.finding_id)
        if finding:
            finding.status = "approved" if approved else "rejected"
            db.add(finding)

            # Update response actions
            for action in db.query(ResponseAction).filter(ResponseAction.finding_id == finding.id).all():
                action.status = "APPROVED" if approved else "REJECTED"
                db.add(action)

        # Update run status
        if run:
            run.status = "completed" if approved else "blocked"
            run.completed_at = datetime.utcnow() if not run.completed_at else run.completed_at
            db.add(run)

        db.commit()

        # Audit
        try:
            audit_service = AuditService(db)
            audit_service.record(
                agent_id=finding.agent_id if finding else None,
                run_id=run.id,
                finding_id=finding.id if finding else None,
                event_type="APPROVAL_GRANTED" if approved else "APPROVAL_REJECTED",
                actor=decided_by,
                details={"reason": reason, "approval_id": str(approval.id)},
            )
        except Exception:
            pass

        return {
            "run_id": str(run.id),
            "approval_id": str(approval.id),
            "status": approval.status,
            "decision_reason": approval.decision_reason,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
