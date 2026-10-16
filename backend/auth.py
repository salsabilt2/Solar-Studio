from datetime import datetime, timedelta, timezone

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from backend.config import settings
from backend.db import get_db
from backend.models import User

hasher = PasswordHasher()
COOKIE_NAME = "solar_session"


def make_token(user: User) -> str:
    return jwt.encode(
        {"sub": str(user.id), "exp": datetime.now(timezone.utc) + timedelta(days=7)},
        settings.secret_key,
        algorithm="HS256",
    )


def current_user(request: Request, db: Session = Depends(get_db)) -> User:
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        raise HTTPException(401, "Sign in to continue.")
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        user_id = int(payload["sub"])
    except (jwt.PyJWTError, ValueError, KeyError) as exc:
        raise HTTPException(401, "Session expired. Sign in again.") from exc
    user = db.get(User, user_id)
    if not user or user.deleted_at:
        raise HTTPException(401, "Account is unavailable.")
    return user


def require_role(*roles: str):
    def dependency(user: User = Depends(current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(403, "This account cannot perform that action.")
        return user

    return dependency


def verify_password(password: str, stored: str) -> bool:
    try:
        return hasher.verify(stored, password)
    except VerifyMismatchError:
        return False


def public_user(user: User) -> dict:
    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "role": user.role,
        "tier": user.tier,
        "company_name": user.company_name,
    }
