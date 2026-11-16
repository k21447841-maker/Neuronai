import uuid
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.api.deps import get_current_user_id
from app.core.config import get_settings
from app.core.security import encrypt_secret
from app.database.session import get_db
from app.models.models import ConnectedChannel, OAuthToken, ScheduledUpload, Upload
from app.schemas.schemas import YouTubeUploadRequest
from app.workers.tasks import youtube_upload_task
from app.youtube.service import create_oauth_flow, fetch_my_channel_info

router = APIRouter(prefix="/api/youtube", tags=["YouTube"])


@router.get("/oauth/start")
def start_youtube_oauth(user_id: UUID = Depends(get_current_user_id)):
    flow = create_oauth_flow(state=str(user_id))
    auth_url, _ = flow.authorization_url(access_type="offline", include_granted_scopes="true", prompt="consent")
    return {"authorization_url": auth_url}


@router.get("/oauth/callback")
def youtube_oauth_callback(code: str = Query(...), state: str = Query(...), db: Session = Depends(get_db)):
    user_id = UUID(state)
    flow = create_oauth_flow(state=state)
    flow.fetch_token(code=code)
    creds = flow.credentials
    info = fetch_my_channel_info(creds)

    ch = db.query(ConnectedChannel).filter(ConnectedChannel.user_id == user_id, ConnectedChannel.youtube_channel_id == info["youtube_channel_id"]).first()
    if not ch:
        ch = ConnectedChannel(user_id=user_id, **info, status="active")
        db.add(ch)
        db.flush()
    else:
        ch.channel_title = info["channel_title"]
        ch.subscriber_count = info["subscriber_count"]
        ch.video_count = info["video_count"]
        ch.status = "active"

    tok = db.query(OAuthToken).filter(OAuthToken.channel_id == ch.id).first()
    if not tok:
        db.add(OAuthToken(user_id=user_id, channel_id=ch.id, encrypted_access_token=encrypt_secret(creds.token), encrypted_refresh_token=encrypt_secret(creds.refresh_token or ""), scopes=" ".join(creds.scopes or []), expires_at=creds.expiry))
    else:
        tok.encrypted_access_token = encrypt_secret(creds.token)
        if creds.refresh_token:
            tok.encrypted_refresh_token = encrypt_secret(creds.refresh_token)
        tok.expires_at = creds.expiry
    db.commit()
    return RedirectResponse(f"{get_settings().PUBLIC_FRONTEND_URL}/youtube-channels?connected=1")


@router.get("/channels")
def list_connected_channels(user_id: UUID = Depends(get_current_user_id), db: Session = Depends(get_db)):
    return [
        {"id": str(c.id), "youtube_channel_id": c.youtube_channel_id, "channel_title": c.channel_title, "channel_handle": c.channel_handle, "thumbnail_url": c.thumbnail_url, "subscriber_count": c.subscriber_count, "video_count": c.video_count, "status": c.status}
        for c in db.query(ConnectedChannel).filter(ConnectedChannel.user_id == user_id).all()
    ]


@router.delete("/channels/{channel_id}")
def disconnect_channel(channel_id: UUID, user_id: UUID = Depends(get_current_user_id), db: Session = Depends(get_db)):
    ch = db.query(ConnectedChannel).filter(ConnectedChannel.id == channel_id, ConnectedChannel.user_id == user_id).first()
    if not ch:
        raise HTTPException(status_code=404, detail="Channel not found")
    db.delete(ch)
    db.commit()
    return {"disconnected": True}


@router.post("/upload")
def upload_or_schedule_video(body: YouTubeUploadRequest, user_id: UUID = Depends(get_current_user_id), db: Session = Depends(get_db)):
    ch = db.query(ConnectedChannel).filter(ConnectedChannel.id == body.channel_id, ConnectedChannel.user_id == user_id).first()
    if not ch or ch.status != "active":
        raise HTTPException(status_code=400, detail="Selected YouTube channel is not active")

    idem_key = f"{user_id}:{body.project_id}:{body.video_id}:{body.channel_id}"
    existing = db.query(Upload).filter(Upload.idempotency_key == idem_key).first()
    if existing:
        return {"upload_id": str(existing.id), "upload_status": existing.upload_status, "youtube_video_id": existing.youtube_video_id}

    upload = Upload(
        id=uuid.uuid4(), user_id=user_id, project_id=body.project_id, channel_id=body.channel_id,
        video_id=body.video_id, thumbnail_image_id=body.thumbnail_image_id, title=body.title,
        description=body.description, tags=body.tags, privacy_status=body.privacy_status,
        is_short=body.is_short, upload_status="pending", idempotency_key=idem_key,
    )
    db.add(upload)
    db.flush()
    if body.scheduled_publish_at:
        db.add(ScheduledUpload(user_id=user_id, upload_id=upload.id, scheduled_for=body.scheduled_publish_at))
        db.commit()
        return {"upload_id": str(upload.id), "upload_status": "scheduled"}
    db.commit()
    youtube_upload_task.delay(str(upload.id))
    return {"upload_id": str(upload.id), "upload_status": "queued"}
