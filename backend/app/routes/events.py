from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..auth import AdminUser, require_admin
from ..models import Agent, ExecutionEvent
from ..schemas import EventResponse


router = APIRouter(prefix="/events", tags=["Events"])


@router.get("", response_model=list[EventResponse])
def get_execution_events(db: Session = Depends(get_db), admin: AdminUser = Depends(require_admin)):
    return (
        db.query(ExecutionEvent)
        .join(Agent, ExecutionEvent.agent_id == Agent.id)
        .filter(Agent.owner_id == admin.id)
        .order_by(ExecutionEvent.id.desc())
        .all()
    )
