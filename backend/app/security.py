from datetime import datetime, timedelta, timezone
import jwt
from pwdlib import PasswordHash
from app.config import get_settings

password_hash = PasswordHash.recommended()


def hash_password(value: str) -> str:
    return password_hash.hash(value)


def verify_password(value: str, hashed: str) -> bool:
    return password_hash.verify(value, hashed)


def create_access_token(subject: str, role: str) -> str:
    settings = get_settings()
    payload = {"sub": subject, "role": role, "type": "access", "exp": datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_access_minutes)}
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def decode_access_token(token: str) -> dict:
    settings = get_settings()
    payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    if payload.get("type") != "access" or not payload.get("sub"):
        raise jwt.InvalidTokenError("invalid access token")
    return payload
