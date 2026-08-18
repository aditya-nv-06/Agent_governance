from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..auth import require_admin, AdminUser
from ..database import get_db
from ..models import EnvAgent, EnvLog, Agent, BehaviorProfile, Finding, AuditEvent, AgentRun
import httpx
import json
import uuid

router = APIRouter(prefix="/env", tags=["Environment Agents"])


class RegisterPayload:
    name: str
    url: str
    purpose: str


@router.post("/agents")
def register_agent(payload: dict, db: Session = Depends(get_db), admin: AdminUser = Depends(require_admin)):
    try:
        name = payload.get("name")
        url = payload.get("url")
        purpose = payload.get("purpose")
        if not name or not url:
            raise HTTPException(status_code=400, detail="name and url are required")
        allowed = payload.get("allowed_instructions") or []
        # normalize to list of strings
        if isinstance(allowed, str):
            allowed = [s.strip() for s in allowed.split(",") if s.strip()]

        agent_id = uuid.uuid4()
        
        # 1. Create EnvAgent
        env_agent = EnvAgent(
            id=agent_id,
            name=name,
            url=url,
            purpose=purpose or None,
            owner_id=admin.id,
            allowed_instructions=allowed,
        )
        db.add(env_agent)

        # 2. Synchronize with primary Agent model so agent counts and details display everywhere
        desc = f"External Agent ({url})"
        if purpose:
            desc += f" · Purpose: {purpose}"
        
        main_agent = Agent(
            id=agent_id,
            name=name,
            description=desc,
            status="active",
            owner_id=admin.id,
        )
        db.add(main_agent)
        db.flush()

        # 3. Create behavior profile for governance boundaries
        profile = BehaviorProfile(
            agent_id=agent_id,
            name=f"{name} Profile",
            allowed_tools=allowed,
            allowed_actions=allowed,
            allowed_data_sources=["external_service", "http_endpoint"],
            max_llm_calls=1000,
            warning_threshold=80,
            critical_threshold=90,
        )
        db.add(profile)

        # 4. Audit log agent registration
        audit = AuditEvent(
            agent_id=agent_id,
            run_id=None,
            finding_id=None,
            event_type="AGENT_REGISTERED",
            actor="admin",
            details={"name": name, "url": url, "allowed_instructions": allowed},
        )
        db.add(audit)

        db.commit()
        db.refresh(env_agent)
        return {
            "id": str(env_agent.id),
            "name": env_agent.name,
            "url": env_agent.url,
            "purpose": env_agent.purpose,
            "allowed_instructions": env_agent.allowed_instructions or [],
            "created_at": env_agent.created_at.isoformat(),
        }
    except Exception as error:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(error)) from error


@router.get("/agents")
def list_agents(db: Session = Depends(get_db), admin: AdminUser = Depends(require_admin)):
    agents = db.query(EnvAgent).filter(EnvAgent.owner_id == admin.id).all()
    return [{"id": str(a.id), "name": a.name, "url": a.url, "purpose": a.purpose, "allowed_instructions": a.allowed_instructions or [], "created_at": a.created_at.isoformat()} for a in agents]


@router.post("/agents/{agent_id}/trigger")
def trigger_agent(agent_id: str, payload: dict, db: Session = Depends(get_db), admin: AdminUser = Depends(require_admin)):
    message = payload.get("message") if payload else None
    if not message:
        raise HTTPException(status_code=400, detail="message is required")

    try:
        agent_uuid = uuid.UUID(agent_id)
    except Exception:
        raise HTTPException(status_code=400, detail="invalid agent id")
    agent = db.get(EnvAgent, agent_uuid)
    if not agent:
        raise HTTPException(status_code=404, detail="agent not found")

    # Create run for trace
    run = AgentRun(
        agent_id=agent.id,
        input_message=message,
        status="running",
    )
    db.add(run)
    db.flush()

    # Forward instructions if provided by caller
    instructions = payload.get("instructions") if payload else None
    request_payload = {"message": message, "purpose": agent.purpose}
    if instructions is not None:
        request_payload["instructions"] = instructions
    try:
        # Enforce per-agent allowed instructions before forwarding
        if instructions:
            disallowed = [ins for ins in instructions if ins not in (agent.allowed_instructions or [])]
            if disallowed:
                # Out of scope: directly blocked, not sent to approval!
                finding = Finding(
                    agent_id=agent.id,
                    run_id=run.id,
                    finding_type="out_of_scope_instruction",
                    severity="HIGH",
                    expected=f"Allowed instructions: {', '.join(agent.allowed_instructions or [])}",
                    actual=f"Disallowed out-of-scope instructions: {', '.join(disallowed)}",
                    reason=f"Instruction is out of scope and directly blocked: {', '.join(disallowed)}",
                    status="open",
                )
                db.add(finding)

                audit = AuditEvent(
                    agent_id=agent.id,
                    run_id=run.id,
                    finding_id=finding.id,
                    event_type="INSTRUCTION_BLOCKED",
                    actor="governance",
                    details={"disallowed": disallowed, "reason": "out_of_scope"},
                )
                db.add(audit)

                run.status = "blocked"

                log = EnvLog(
                    agent_id=agent.id,
                    request={"message": message, "instructions": instructions},
                    response={"status": "blocked", "message": "Instruction is out of scope and directly blocked.", "disallowed": disallowed},
                    status_code=200,
                )
                db.add(log)
                db.commit()
                return {
                    "status": "blocked",
                    "governance": "BLOCKED",
                    "message": f"Action is out of scope and directly blocked: {', '.join(disallowed)}",
                    "disallowed": disallowed,
                    "finding_id": str(finding.id),
                }

        resp = httpx.post(agent.url, json=request_payload, timeout=10.0)
        try:
            content = resp.json()
        except Exception:
            content = resp.text

        run.status = "completed"
        log = EnvLog(agent_id=agent.id, request=request_payload, response=content if isinstance(content, (dict, list)) else {"text": str(content)}, status_code=resp.status_code)
        db.add(log)
        db.commit()
        return {"status": "ok", "log_id": str(log.id), "response": content, "status_code": resp.status_code}
    except Exception as error:
        run.status = "failed"
        log = EnvLog(agent_id=agent.id, request=request_payload, response={"error": str(error)}, status_code=None)
        db.add(log)
        db.commit()
        raise HTTPException(status_code=502, detail=str(error)) from error



@router.get("/logs")
def get_logs(agent_id: str | None = None, db: Session = Depends(get_db), admin: AdminUser = Depends(require_admin)):
    q = db.query(EnvLog).order_by(EnvLog.created_at.desc())
    if agent_id and agent_id.lower() != "null":
        try:
            aid = uuid.UUID(agent_id)
            q = q.filter(EnvLog.agent_id == aid)
        except Exception:
            raise HTTPException(status_code=400, detail="invalid agent id")
    logs = q.limit(200).all()
    out = []
    for l in logs:
        out.append({
            "id": str(l.id),
            "agent_id": str(l.agent_id),
            "request": l.request,
            "response": l.response,
            "status_code": l.status_code,
            "timestamp": l.created_at.isoformat(),
        })
    return out
