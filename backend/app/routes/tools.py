from fastapi import APIRouter

from ..agent.tools import list_tools


router = APIRouter(prefix="/tools", tags=["Tools"])


@router.get("")
def get_tools():
    """Return the registry names exposed to the deterministic demo agent."""
    return {"tools": list_tools()}
