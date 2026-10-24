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


def get_current_user(request: Request, db: Session = Depends(get_db)) -> CurrentUser:
    """Authenticate a bearer token or the HttpOnly session cookie."""
    from backend.src.auth import authenticate

    authorization = request.headers.get("authorization", "")
    token = (
        authorization[7:].strip()
        if authorization.lower().startswith("bearer ")
        else request.cookies.get("access_token")
    )
    user = authenticate(token, db) if token else None
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "UNAUTHENTICATED", "message": "Authentication required"},
            headers={"WWW-Authenticate": "Bearer"},
        )
    request.state.user = user
    return user


def require_role(role: str):
    def dependency(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if user.role != role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "FORBIDDEN",
                    "message": "Action is not allowed for this role",
                },
            )
        return user

    return dependency
