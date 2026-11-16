from datetime import datetime, timezone
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import get_current_user_id
from app.core.security import decrypt_secret, encrypt_secret, mask_api_key
from app.database.session import get_db
from app.models.models import AIProvider, APICredential
from app.providers.elevenlabs_adapter import ElevenLabsAdapter
from app.providers.llm_adapters import get_llm_provider
from app.providers.visual_adapters import VisualGenerationAdapter
from app.schemas.schemas import ProviderCredentialUpsert

router = APIRouter(prefix="/api/providers", tags=["Providers"])


@router.get("")
def list_providers(user_id: UUID = Depends(get_current_user_id), db: Session = Depends(get_db)):
    catalog = db.query(AIProvider).filter(AIProvider.is_active == True).all()
    creds = {c.provider_slug: c for c in db.query(APICredential).filter(APICredential.user_id == user_id).all()}
    return [
        {
            "slug": p.slug, "display_name": p.display_name, "category": p.category,
            "default_model": p.default_model, "available_models": p.available_models,
            "supports_multimodal": p.supports_multimodal, "configured": p.slug in creds,
            "key_hint": creds[p.slug].key_hint if p.slug in creds else None,
            "selected_model": creds[p.slug].selected_model if p.slug in creds else p.default_model,
            "is_enabled": creds[p.slug].is_enabled if p.slug in creds else False,
            "connection_status": creds[p.slug].connection_status if p.slug in creds else "unconfigured",
            "last_error": creds[p.slug].last_error if p.slug in creds else None,
            "timeout_seconds": creds[p.slug].timeout_seconds if p.slug in creds else 60,
            "max_retries": creds[p.slug].max_retries if p.slug in creds else 2,
            "task_routing": creds[p.slug].task_routing if p.slug in creds else {},
        }
        for p in catalog
    ]


@router.put("")
def upsert_provider(body: ProviderCredentialUpsert, user_id: UUID = Depends(get_current_user_id), db: Session = Depends(get_db)):
    if not db.query(AIProvider).filter(AIProvider.slug == body.provider_slug).first():
        raise HTTPException(status_code=404, detail="Unknown provider slug")
    cred = db.query(APICredential).filter(APICredential.user_id == user_id, APICredential.provider_slug == body.provider_slug).first()
    if not cred:
        if not body.api_key:
            raise HTTPException(status_code=400, detail="API key is required for initial setup")
        cred = APICredential(
            user_id=user_id, provider_slug=body.provider_slug, encrypted_api_key=encrypt_secret(body.api_key.strip()),
            key_hint=mask_api_key(body.api_key.strip()), selected_model=body.selected_model, is_enabled=body.is_enabled,
            timeout_seconds=body.timeout_seconds, max_retries=body.max_retries, task_routing=body.task_routing, connection_status="unverified",
        )
        db.add(cred)
    else:
        if body.api_key:
            cred.encrypted_api_key = encrypt_secret(body.api_key.strip())
            cred.key_hint = mask_api_key(body.api_key.strip())
            cred.connection_status = "unverified"
        cred.selected_model = body.selected_model
        cred.is_enabled = body.is_enabled
        cred.timeout_seconds = body.timeout_seconds
        cred.max_retries = body.max_retries
        cred.task_routing = body.task_routing
    db.commit()
    return {"status": "saved", "provider_slug": cred.provider_slug, "key_hint": cred.key_hint}


@router.post("/{provider_slug}/test")
async def test_provider_connection(provider_slug: str, user_id: UUID = Depends(get_current_user_id), db: Session = Depends(get_db)):
    cred = db.query(APICredential).filter(APICredential.user_id == user_id, APICredential.provider_slug == provider_slug).first()
    if not cred:
        raise HTTPException(status_code=404, detail="Provider credentials not configured")
    api_key = decrypt_secret(cred.encrypted_api_key)
    meta = db.query(AIProvider).filter(AIProvider.slug == provider_slug).first()
    try:
        if meta.category == "llm":
            res = await get_llm_provider(provider_slug).test_connection(api_key, cred.selected_model, cred.timeout_seconds)
        elif provider_slug == "elevenlabs":
            res = await ElevenLabsAdapter().test_and_get_subscription(api_key)
        elif meta.category == "visual":
            res = await VisualGenerationAdapter().test_connection(provider_slug, api_key)
        else:
            raise HTTPException(status_code=400, detail="Unsupported provider test")
        cred.connection_status = "connected"
        cred.last_error = None
        cred.last_checked_at = datetime.now(timezone.utc)
        db.commit()
        return res
    except HTTPException as exc:
        cred.connection_status = "error"
        cred.last_error = exc.detail
        cred.last_checked_at = datetime.now(timezone.utc)
        db.commit()
        raise
