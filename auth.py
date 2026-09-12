"""
Authentication & role-based scoping for the 4 SIH26102 personas
(MP, State Nodal Authority, District Authority, Ministry).

Kept deliberately small: password hashing + JWT issuing/verification +
a couple of FastAPI dependencies that every data endpoint can use to
scope its query. No permissions matrix, no per-action ACLs — one role,
one scope column, per Epic 1 of mdfiles/PRD_GAP_CLOSURE.md.
"""

import os
import secrets
from datetime import date, datetime, timedelta, timezone
from typing import Optional

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from db import get_db
from models import User, UserRole, WorkRecommendation

INVITE_EXPIRY_DAYS = 7

# In production this MUST come from an env var. A hardcoded fallback is
# fine for a prototype/demo but is called out here so it isn't missed.
JWT_SECRET = os.environ.get("JWT_SECRET", "nirikshak-ai-dev-secret-change-me")
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = 12

bearer_scheme = HTTPBearer(auto_error=False)


def hash_password(plain_password: str) -> str:
    return bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), password_hash.encode("utf-8"))


def create_access_token(user: User) -> str:
    payload = {
        "sub": str(user.id),
        "email": user.email,
        "role": user.role.value,
        "scope_id": user.scope_id,
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRY_HOURS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid auth token")


class CurrentUser:
    """Lightweight view of the JWT claims — no DB hit needed per request."""

    def __init__(self, user_id: int, email: str, role: UserRole, scope_id: Optional[str]):
        self.id = user_id
        self.email = email
        self.role = role
        self.scope_id = scope_id

    @property
    def is_ministry(self) -> bool:
        return self.role == UserRole.MINISTRY


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> CurrentUser:
    """
    Validates the JWT AND re-checks the account against the DB on every
    request (not just at login). This costs one extra query per request
    but means deactivating a user (Ministry toggle) takes effect
    immediately, even against a JWT issued minutes ago and not yet
    expired — a stale-claims-only check couldn't do that.
    """
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    claims = decode_access_token(credentials.credentials)
    user = db.query(User).filter(User.id == int(claims["sub"])).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Account disabled or not found")
    return CurrentUser(
        user_id=user.id,
        email=user.email,
        role=user.role,
        scope_id=user.scope_id,
    )


def require_role(*allowed_roles: UserRole):
    """FastAPI dependency factory: restrict an endpoint to specific roles."""

    def _dependency(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{user.role.value}' cannot access this resource",
            )
        return user

    return _dependency


def scope_works_query(query, user: CurrentUser):
    """
    Apply the caller's role/scope to a SQLAlchemy query over
    WorkRecommendation. Ministry sees everything; MP sees only their
    own works; State Nodal / District filter by location fields.

    Server-side enforced — a caller cannot widen this via query params.
    """
    if user.role == UserRole.MINISTRY:
        return query
    if user.role == UserRole.MP:
        return query.filter(WorkRecommendation.mp_id == int(user.scope_id))
    if user.role == UserRole.STATE_NODAL:
        return query.filter(WorkRecommendation.work_location_state == user.scope_id)
    if user.role == UserRole.DISTRICT:
        return query.filter(WorkRecommendation.work_location_district == user.scope_id)
    return query.filter(False)  # unknown role — fail closed, not open


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    user = db.query(User).filter(User.email == email.lower().strip()).first()
    if not user or not user.password_hash or not user.is_active:
        return None  # unknown email, invite not yet accepted, or deactivated
    if not verify_password(password, user.password_hash):
        return None
    return user


def create_invited_user(
    db: Session, email: str, full_name: str, role: UserRole, scope_id: Optional[str]
) -> User:
    """
    Provision an account with no password: it's unusable for login
    until the invitee calls POST /auth/accept-invite with the token
    this returns on the User object. Ministry never sees or sets the
    invitee's password.
    """
    existing = db.query(User).filter(User.email == email.lower().strip()).first()
    if existing:
        raise HTTPException(status_code=409, detail="A user with this email already exists")

    user = User(
        email=email.lower().strip(),
        password_hash=None,
        full_name=full_name,
        role=role,
        scope_id=scope_id,
        created_at=date.today(),
        invite_token=secrets.token_urlsafe(32),
        invite_expires_at=date.today() + timedelta(days=INVITE_EXPIRY_DAYS),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def reissue_invite(db: Session, user: User) -> User:
    """Generate a fresh invite token (e.g. the old one expired or was lost)."""
    user.invite_token = secrets.token_urlsafe(32)
    user.invite_expires_at = date.today() + timedelta(days=INVITE_EXPIRY_DAYS)
    db.commit()
    db.refresh(user)
    return user


def set_user_active(db: Session, user: User, is_active: bool) -> User:
    """Ministry-triggered enable/disable. Enforced immediately — see get_current_user."""
    user.is_active = is_active
    db.commit()
    db.refresh(user)
    return user


def accept_invite(db: Session, token: str, new_password: str) -> User:
    """
    First-login password set: the invitee proves they hold the invite
    token (from an emailed/shared link) and picks their own password.
    This is the only way an invited account becomes loginable.
    """
    user = db.query(User).filter(User.invite_token == token).first()
    if not user:
        raise HTTPException(status_code=404, detail="Invalid or already-used invite link")
    if user.invite_expires_at and user.invite_expires_at < date.today():
        raise HTTPException(status_code=410, detail="This invite link has expired — ask for a new one")
    if len(new_password) < 8:
        raise HTTPException(status_code=422, detail="Password must be at least 8 characters")

    user.password_hash = hash_password(new_password)
    user.invite_token = None
    user.invite_expires_at = None
    db.commit()
    db.refresh(user)
    return user


def seed_demo_users(db: Session) -> None:
    """
    Seed one demo login per persona so the 4-role flow is demoable out
    of the box. scope_id values match the seeded MP (id=1, Gorakhpur,
    Uttar Pradesh) from db.seed_sample_data — keep these in sync if that
    seed data changes.

    These bypass the invite flow on purpose (password set directly) so
    the demo works with zero setup — real accounts should go through
    create_invited_user() / POST /admin/users instead.
    """
    if db.query(User).count() > 0:
        return

    demo_users = [
        ("mp@nirikshak.demo", "MP Demo Account", UserRole.MP, "1"),
        ("state.up@nirikshak.demo", "UP State Nodal Authority", UserRole.STATE_NODAL, "Uttar Pradesh"),
        ("district.gorakhpur@nirikshak.demo", "Gorakhpur District Authority", UserRole.DISTRICT, "Gorakhpur"),
        ("ministry@nirikshak.demo", "Ministry of Statistics & PI", UserRole.MINISTRY, None),
    ]
    for email, name, role, scope_id in demo_users:
        db.add(User(
            email=email,
            password_hash=hash_password("demo1234"),
            full_name=name,
            role=role,
            scope_id=scope_id,
            created_at=date.today(),
        ))
    db.commit()
