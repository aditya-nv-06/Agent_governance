import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..auth import AdminUser, get_owned_agent, require_admin
from ..models import Agent, BehaviorProfile
from ..schemas import ProfileCreate, ProfileResponse


router = APIRouter(prefix="/profiles", tags=["Behavior profiles"])


@router.get("", response_model=list[ProfileResponse])
def list_profiles(db: Session = Depends(get_db), admin: AdminUser = Depends(require_admin)):
    return (
        db.query(BehaviorProfile)
        .join(Agent, BehaviorProfile.agent_id == Agent.id)
        .filter(Agent.owner_id == admin.id)
        .order_by(BehaviorProfile.name)
        .all()
    )


@router.post("", response_model=ProfileResponse, status_code=201)
def create_profile(payload: ProfileCreate, db: Session = Depends(get_db), admin: AdminUser = Depends(require_admin)):
    get_owned_agent(db, payload.agent_id, admin)
    profile = BehaviorProfile(**payload.model_dump())
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


@router.put("/{profile_id}", response_model=ProfileResponse)
def update_profile(profile_id: uuid.UUID, payload: ProfileCreate, db: Session = Depends(get_db), admin: AdminUser = Depends(require_admin)):
    profile = (
        db.query(BehaviorProfile)
        .join(Agent, BehaviorProfile.agent_id == Agent.id)
        .filter(BehaviorProfile.id == profile_id, Agent.owner_id == admin.id)
        .first()
    )
    if not profile:
        raise HTTPException(status_code=404, detail="Behavior profile not found")
    get_owned_agent(db, payload.agent_id, admin)

    for field, value in payload.model_dump().items():
        setattr(profile, field, value)
    db.commit()
    db.refresh(profile)
    return profile
