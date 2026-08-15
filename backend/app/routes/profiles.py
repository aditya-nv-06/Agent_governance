import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Agent, BehaviorProfile
from ..schemas import ProfileCreate, ProfileResponse


router = APIRouter(prefix="/profiles", tags=["Behavior profiles"])


@router.get("", response_model=list[ProfileResponse])
def list_profiles(db: Session = Depends(get_db)):
    return db.query(BehaviorProfile).order_by(BehaviorProfile.name).all()


@router.post("", response_model=ProfileResponse, status_code=201)
def create_profile(payload: ProfileCreate, db: Session = Depends(get_db)):
    if not db.get(Agent, payload.agent_id):
        raise HTTPException(status_code=404, detail="Agent not found")
    profile = BehaviorProfile(**payload.model_dump())
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


@router.put("/{profile_id}", response_model=ProfileResponse)
def update_profile(profile_id: uuid.UUID, payload: ProfileCreate, db: Session = Depends(get_db)):
    profile = db.get(BehaviorProfile, profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Behavior profile not found")
    if not db.get(Agent, payload.agent_id):
        raise HTTPException(status_code=404, detail="Agent not found")

    for field, value in payload.model_dump().items():
        setattr(profile, field, value)
    db.commit()
    db.refresh(profile)
    return profile
