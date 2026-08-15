from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..auth import create_access_token, create_password_fields, require_admin, verify_password
from ..database import get_db
from ..models import AdminUser
from ..schemas import AdminLoginRequest, AdminRegisterRequest, AuthResponse, AdminResponse


router = APIRouter(prefix="/auth", tags=["Authentication"])

import logging
logger = logging.getLogger(__name__)


def response_for(admin: AdminUser) -> AuthResponse:
    return AuthResponse(access_token=create_access_token(admin), admin=AdminResponse.model_validate(admin))


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(payload: AdminRegisterRequest, db: Session = Depends(get_db)):
    email = payload.email.strip().lower()
    if db.query(AdminUser).filter(AdminUser.email == email).first():
        raise HTTPException(status_code=409, detail="An admin account already exists for this email")
    salt, password_hash = create_password_fields(payload.password)
    admin = AdminUser(email=email, password_salt=salt, password_hash=password_hash, role="admin")
    db.add(admin)
    db.commit()
    db.refresh(admin)
    logger.info("Registered admin: %s", email)
    return response_for(admin)


@router.post("/login", response_model=AuthResponse)
def login(payload: AdminLoginRequest, db: Session = Depends(get_db)):
    admin = db.query(AdminUser).filter(AdminUser.email == payload.email.strip().lower()).first()
    if not admin or not verify_password(payload.password, admin):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return response_for(admin)


@router.get("/me", response_model=AdminResponse)
def current_admin(admin: AdminUser = Depends(require_admin)):
    return admin
