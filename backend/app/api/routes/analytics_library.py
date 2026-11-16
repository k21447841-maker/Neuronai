from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.api.deps import get_current_user_id
from app.database.session import get_db
from app.models.models import (
    ConnectedChannel, GeneratedAudio, GeneratedImage, GeneratedVideo,
    OAuthToken, RenderingJob, ScheduledUpload, Upload, UsageLog
)
from app.youtube.service import credentials_from_encrypted_row, fetch_uploaded_video_metrics

router = APIRouter(prefix="/api", tags=["Analytics, Library & Usage"])


@router.get("/analytics/overview")
def get_dashboard_overview(user_id: UUID = Depends(get_current_user_id), db: Session = Depends(get_db)):
    total_videos = db.query(func.count(GeneratedVideo.id)).filter(GeneratedVideo.user_id == user_id, GeneratedVideo.video_kind == "final_render").scalar() or 0
    published = db.query(func.count(Upload.id)).filter(Upload.user_id == user_id, Upload.upload_status == "uploaded").scalar() or 0
    scheduled = db.query(func.count(ScheduledUpload.id)).filter(ScheduledUpload.user_id == user_id, ScheduledUpload.status == "scheduled").scalar() or 0
    failed_jobs = db.query(func.count(RenderingJob.id)).filter(RenderingJob.user_id == user_id, RenderingJob.status == "failed").scalar() or 0
    channels = db.query(func.count(ConnectedChannel.id)).filter(ConnectedChannel.user_id == user_id, ConnectedChannel.status == "active").scalar() or 0
    voice_chars = db.query(func.coalesce(func.sum(UsageLog.units_consumed), 0)).filter(UsageLog.user_id == user_id, UsageLog.provider_slug == "elevenlabs").scalar() or 0
    return {
        "total_generated_videos": total_videos, "total_published_videos": published,
        "total_scheduled_videos": scheduled, "failed_generation_jobs": failed_jobs,
        "connected_channels": channels, "voice_characters_used": float(voice_chars),
    }


@router.get("/analytics/youtube")
def get_youtube_video_metrics(user_id: UUID = Depends(get_current_user_id), db: Session = Depends(get_db)):
    channels = db.query(ConnectedChannel).filter(ConnectedChannel.user_id == user_id, ConnectedChannel.status == "active").all()
    metrics = []
    for ch in channels:
        yt_ids = [u.youtube_video_id for u in db.query(Upload).filter(Upload.channel_id == ch.id, Upload.youtube_video_id.isnot(None)).all() if u.youtube_video_id]
        if not yt_ids:
            continue
        tok = db.query(OAuthToken).filter(OAuthToken.channel_id == ch.id).first()
        if not tok:
            continue
        creds = credentials_from_encrypted_row(tok)
        db.commit()
        metrics.extend(fetch_uploaded_video_metrics(creds, yt_ids))
    return {"videos": metrics}


@router.get("/library")
def get_content_library(user_id: UUID = Depends(get_current_user_id), db: Session = Depends(get_db)):
    images = db.query(GeneratedImage).filter(GeneratedImage.user_id == user_id).order_by(GeneratedImage.created_at.desc()).limit(50).all()
    videos = db.query(GeneratedVideo).filter(GeneratedVideo.user_id == user_id).order_by(GeneratedVideo.created_at.desc()).limit(50).all()
    audios = db.query(GeneratedAudio).filter(GeneratedAudio.user_id == user_id).order_by(GeneratedAudio.created_at.desc()).limit(50).all()
    return {
        "images": [{"id": str(i.id), "prompt": i.prompt, "url": i.public_url, "kind": i.asset_kind, "created_at": i.created_at.isoformat()} for i in images],
        "videos": [{"id": str(v.id), "url": v.public_url, "resolution": v.resolution, "kind": v.video_kind, "created_at": v.created_at.isoformat()} for v in videos],
        "audios": [{"id": str(a.id), "voice_name": a.voice_name, "duration_seconds": float(a.duration_seconds), "created_at": a.created_at.isoformat()} for a in audios],
    }


@router.get("/usage")
def get_usage_logs(user_id: UUID = Depends(get_current_user_id), db: Session = Depends(get_db)):
    logs = db.query(UsageLog).filter(UsageLog.user_id == user_id).order_by(UsageLog.created_at.desc()).limit(100).all()
    return [
        {"id": str(l.id), "provider_slug": l.provider_slug, "operation": l.operation, "units_consumed": float(l.units_consumed), "unit_type": l.unit_type, "created_at": l.created_at.isoformat()}
        for l in logs
    ]
