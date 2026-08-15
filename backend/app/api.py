from fastapi import APIRouter

from .routes import agents, approvals, audit, findings, profiles, run,agent


api_router = APIRouter()
api_router.include_router(agents.router)
api_router.include_router(profiles.router)
api_router.include_router(run.router)
api_router.include_router(findings.router)
api_router.include_router(approvals.router)
api_router.include_router(audit.router)
api_router.include_router(agent.router)
