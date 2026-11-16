from uuid import UUID
from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session
from app.core.security import decrypt_secret, verify_supabase_jwt
from app.database.session import get_db
from app.models.models import APICredential, Profile


def get_current_user_id(authorization: str = Header(default="")) -> UUID:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Bearer token")
    claims = verify_supabase_jwt(authorization.split(" ", 1)[1].strip())
    return UUID(claims["sub"])


def require_admin(user_id: UUID = Depends(get_current_user_id), db: Session = Depends(get_db)) -> UUID:
    profile = db.query(Profile).filter(Profile.id == user_id).first()
    if not profile or profile.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin privileges required")
    return user_id


def get_decrypted_provider_credential(db: Session, user_id: UUID, provider_slug: str):
    cred = db.query(APICredential).filter(APICredential.user_id == user_id, APICredential.provider_slug == provider_slug).first()
    if not cred or not cred.is_enabled:
        raise HTTPException(status_code=424, detail=f"Provider '{provider_slug}' is not configured or disabled.")
    return cred, decrypt_secret(cred.encrypted_api_key)
