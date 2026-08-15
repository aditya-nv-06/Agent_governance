from fastapi import APIRouter, Depends

from .auth import require_admin
from .routes import agents, approvals, audit, auth, events, findings, profiles, run, tools

api_router = APIRouter()
admin_only = [Depends(require_admin)]
api_router.include_router(auth.router)
api_router.include_router(agents.router, dependencies=admin_only)
api_router.include_router(profiles.router, dependencies=admin_only)
api_router.include_router(run.router, dependencies=admin_only)
api_router.include_router(findings.router, dependencies=admin_only)
api_router.include_router(approvals.router, dependencies=admin_only)
api_router.include_router(audit.router, dependencies=admin_only)
api_router.include_router(tools.router, dependencies=admin_only)
api_router.include_router(events.router, dependencies=admin_only)
api_router.add_api_route(
    "/audit-events",
    audit.get_audit_events,
    methods=["GET"],
    tags=["Audit"],
    dependencies=admin_only,
    include_in_schema=False,
)
api_router.add_api_route(
    "/agent/decide",
    agents.decide,
    methods=["POST"],
    tags=["Agents"],
    dependencies=admin_only,
    include_in_schema=False,
)
api_router.add_api_route(
    "/agent/run",
    run.create_run,
    methods=["POST"],
    tags=["Runs"],
    dependencies=admin_only,
    include_in_schema=False,
)
