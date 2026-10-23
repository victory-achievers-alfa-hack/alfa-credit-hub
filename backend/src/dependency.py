from dataclasses import dataclass
from typing import Generator

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from backend.src.database import SessionLocal


def get_db() -> Generator[Session, None, None]:
    with SessionLocal() as db:
        yield db


@dataclass(frozen=True)
class CurrentUser:
    id: str
    role: str
    company_id: str | None = None


def get_current_user(request: Request) -> CurrentUser:
    """Read the authenticated principal installed by the auth middleware."""
    user = getattr(request.state, "user", None)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "UNAUTHENTICATED", "message": "Authentication required"},
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def require_role(role: str):
    def dependency(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if user.role != role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "FORBIDDEN", "message": "Action is not allowed for this role"},
            )
        return user

    return dependency
