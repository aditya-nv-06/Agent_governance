from fastapi import APIRouter, Depends

from .auth import require_admin
from .routes import agents, approvals, audit, auth, events, findings, profiles, run, tools, simulate
from .routes import environment, external_integration

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
api_router.include_router(simulate.router, dependencies=admin_only)
api_router.include_router(environment.router, dependencies=admin_only)

# External integration routes (no auth required)
api_router.include_router(external_integration.router)
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
