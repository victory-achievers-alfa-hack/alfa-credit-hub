from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time

from sqlalchemy.orm import Session

from backend.src.config import settings
from backend.src.dependency import CurrentUser
from backend.src.models import User


ACCESS_TOKEN_TTL_SECONDS = 60 * 60 * 12
PASSWORD_HASH_ITERATIONS = 310_000


def _encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def create_access_token(user: User) -> str:
    now = int(time.time())
    payload = {
        "sub": user.public_id,
        "role": user.role,
        "company_id": user.company_id,
        "iat": now,
        "exp": now + ACCESS_TOKEN_TTL_SECONDS,
    }
    encoded_payload = _encode(
        json.dumps(payload, separators=(",", ":")).encode("utf-8")
    )
    signature = hmac.new(
        settings.auth_secret.get_secret_value().encode("utf-8"),
        encoded_payload.encode("ascii"),
        hashlib.sha256,
    ).digest()
    return f"{encoded_payload}.{_encode(signature)}"


def authenticate(token: str | None, db: Session) -> CurrentUser | None:
    if not token:
        return None
    try:
        encoded_payload, encoded_signature = token.split(".", maxsplit=1)
        expected_signature = hmac.new(
            settings.auth_secret.get_secret_value().encode("utf-8"),
            encoded_payload.encode("ascii"),
            hashlib.sha256,
        ).digest()
        if not hmac.compare_digest(_decode(encoded_signature), expected_signature):
            return None
        payload = json.loads(_decode(encoded_payload))
        if not isinstance(payload, dict) or int(payload["exp"]) <= int(time.time()):
            return None
        public_id = payload["sub"]
        if not isinstance(public_id, str):
            return None
    except (ValueError, TypeError, KeyError, json.JSONDecodeError, UnicodeDecodeError):
        return None

    user = db.query(User).filter(User.public_id == public_id).one_or_none()
    if user is None or payload.get("role") != user.role:
        return None
    if payload.get("company_id") != user.company_id:
        return None
    return CurrentUser(id=user.public_id, role=user.role, company_id=user.company_id)


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, PASSWORD_HASH_ITERATIONS
    )
    return f"pbkdf2_sha256${PASSWORD_HASH_ITERATIONS}${_encode(salt)}${_encode(digest)}"


def verify_password(password: str, encoded_hash: str) -> bool:
    try:
        algorithm, iterations, salt, expected = encoded_hash.split("$", maxsplit=3)
        rounds = int(iterations)
        if algorithm != "pbkdf2_sha256" or not 100_000 <= rounds <= 1_000_000:
            return False
        actual = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), _decode(salt), rounds
        )
        return hmac.compare_digest(actual, _decode(expected))
    except (ValueError, TypeError, UnicodeDecodeError):
        return False
