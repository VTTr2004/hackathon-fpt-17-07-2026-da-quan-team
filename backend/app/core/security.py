import base64
import hashlib
import hmac
import json
import secrets
import time
from uuid import UUID

from app.core.config import get_settings

PBKDF2_ITERATIONS = 310_000


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, PBKDF2_ITERATIONS)
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, iterations, salt, expected = encoded.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        actual = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), int(iterations))
        return hmac.compare_digest(actual.hex(), expected)
    except (TypeError, ValueError):
        return False


def _b64encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode()


def _b64decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def create_access_token(user_id: UUID) -> str:
    settings = get_settings()
    payload = json.dumps(
        {"sub": str(user_id), "exp": int(time.time()) + settings.auth_token_ttl_hours * 3600},
        separators=(",", ":"),
    ).encode()
    body = _b64encode(payload)
    signature = hmac.new(settings.auth_secret.encode(), body.encode(), hashlib.sha256).digest()
    return f"{body}.{_b64encode(signature)}"


def decode_access_token(token: str) -> UUID | None:
    try:
        body, signature = token.split(".", 1)
        settings = get_settings()
        expected = hmac.new(settings.auth_secret.encode(), body.encode(), hashlib.sha256).digest()
        if not hmac.compare_digest(expected, _b64decode(signature)):
            return None
        payload = json.loads(_b64decode(body))
        if int(payload["exp"]) < int(time.time()):
            return None
        return UUID(payload["sub"])
    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
        return None
