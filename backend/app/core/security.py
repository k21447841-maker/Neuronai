from datetime import datetime, timezone
from typing import Any, Dict
from cryptography.fernet import Fernet, InvalidToken
from fastapi import HTTPException, status
from jose import JWTError, jwt
from app.core.config import get_settings


def _get_fernet() -> Fernet:
    return Fernet(get_settings().CREDENTIAL_ENCRYPTION_KEY.encode("utf-8"))


def encrypt_secret(plaintext: str) -> str:
    if not plaintext:
        return ""
    return _get_fernet().encrypt(plaintext.encode("utf-8")).decode("utf-8")


def decrypt_secret(ciphertext: str) -> str:
    if not ciphertext:
        return ""
    try:
        return _get_fernet().decrypt(ciphertext.encode("utf-8")).decode("utf-8")
    except InvalidToken as exc:
        raise HTTPException(status_code=500, detail="Stored credential could not be decrypted.") from exc


def mask_api_key(key: str) -> str:
    return "****" if len(key) <= 8 else f"{key[:4]}...{key[-4:]}"


def verify_supabase_jwt(token: str) -> Dict[str, Any]:
    try:
        payload = jwt.decode(
            token, get_settings().SUPABASE_JWT_SECRET, algorithms=["HS256"], audience="authenticated"
        )
        exp = payload.get("exp")
        if exp and datetime.fromtimestamp(exp, tz=timezone.utc) < datetime.now(timezone.utc):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
        if not payload.get("sub"):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token subject")
        return payload
    except JWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication token") from exc
