import base64
import hashlib
import hmac
import json
import os
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
import uuid

from .database import get_db
from .models import AdminUser, Agent


TOKEN_TTL_HOURS = 12
bearer_scheme = HTTPBearer(auto_error=False)


def hash_password(password: str, salt: str) -> str:
    return hashlib.scrypt(password.encode(), salt=salt.encode(), n=2**14, r=8, p=1).hex()


def create_password_fields(password: str) -> tuple[str, str]:
    salt = secrets.token_urlsafe(32)
    return salt, hash_password(password, salt)


def verify_password(password: str, admin: AdminUser) -> bool:
    return hmac.compare_digest(hash_password(password, admin.password_salt), admin.password_hash)


def _secret() -> bytes:
    value = os.getenv("AUTH_SECRET", "development-secret-change-before-deployment")
    return value.encode()


def _encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode()


def _decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def create_access_token(admin: AdminUser) -> str:
    payload = {"sub": str(admin.id), "role": "admin", "exp": int((datetime.now(timezone.utc) + timedelta(hours=TOKEN_TTL_HOURS)).timestamp())}
    encoded = _encode(json.dumps(payload, separators=(",", ":")).encode())
    signature = _encode(hmac.new(_secret(), encoded.encode(), hashlib.sha256).digest())
    return f"{encoded}.{signature}"


def require_admin(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> AdminUser:
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Admin login is required")
    try:
        encoded, signature = credentials.credentials.split(".", 1)
        expected = _encode(hmac.new(_secret(), encoded.encode(), hashlib.sha256).digest())
        payload = json.loads(_decode(encoded))
        if not hmac.compare_digest(signature, expected) or payload["role"] != "admin" or payload["exp"] < int(datetime.now(timezone.utc).timestamp()):
            raise ValueError
        # token sub is a UUID string; convert to uuid.UUID for SQLAlchemy when as_uuid=True
        try:
            sub_uuid = uuid.UUID(payload["sub"]) if isinstance(payload.get("sub"), str) else payload.get("sub")
        except Exception:
            sub_uuid = payload.get("sub")
        admin = db.get(AdminUser, sub_uuid)
    except (ValueError, KeyError, json.JSONDecodeError):
        admin = None
    if not admin or admin.role != "admin":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired admin session")
    return admin


def get_owned_agent(db: Session, agent_id, admin: AdminUser) -> Agent:
    agent = db.get(Agent, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent
