import uuid
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from supabase import create_client
from app.api.deps import get_current_user_id, get_decrypted_provider_credential
from app.core.config import get_settings
from app.database.session import get_db
from app.models.models import GeneratedAudio, RenderingJob, UsageLog
from app.providers.elevenlabs_adapter import ElevenLabsAdapter
from app.schemas.schemas import AudioEditRequest, VoiceGenerateRequest
from app.workers.tasks import generate_subtitles_job, process_audio_job

router = APIRouter(prefix="/api/voice", tags=["Voice & Audio"])


@router.get("/library")
async def get_elevenlabs_voices(user_id: UUID = Depends(get_current_user_id), db: Session = Depends(get_db)):
    _, api_key = get_decrypted_provider_credential(db, user_id, "elevenlabs")
    return {"voices": await ElevenLabsAdapter().list_voices(api_key)}


@router.post("/generate")
async def generate_voiceover(body: VoiceGenerateRequest, user_id: UUID = Depends(get_current_user_id), db: Session = Depends(get_db)):
    _, api_key = get_decrypted_provider_credential(db, user_id, "elevenlabs")
    audio_bytes = await ElevenLabsAdapter().synthesize(
        api_key, body.voice_id, body.text, body.model_id, body.stability, body.similarity_boost, body.style, body.speed
    )
    settings = get_settings()
    sb = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
    audio_id = uuid.uuid4()
    storage_path = f"{user_id}/audio/{audio_id}.mp3"
    sb.storage.from_("neuroflow-media").upload(storage_path, audio_bytes, {"content-type": "audio/mpeg", "upsert": "true"})
    signed = sb.storage.from_("neuroflow-media").create_signed_url(storage_path, 3600)["signedURL"]

    db.add(GeneratedAudio(
        id=audio_id, user_id=user_id, project_id=body.project_id, scene_id=body.scene_id,
        provider_slug="elevenlabs", voice_id=body.voice_id, voice_name=body.voice_name,
        storage_path=storage_path, settings={"stability": body.stability, "similarity_boost": body.similarity_boost, "speed": body.speed},
    ))
    db.add(UsageLog(user_id=user_id, provider_slug="elevenlabs", operation="tts_generation", units_consumed=len(body.text), unit_type="characters"))
    db.commit()
    return {"audio_id": str(audio_id), "audio_url": signed, "storage_path": storage_path}


@router.post("/audio/edit")
def enqueue_audio_edit(body: AudioEditRequest, user_id: UUID = Depends(get_current_user_id), db: Session = Depends(get_db)):
    audio = db.query(GeneratedAudio).filter(GeneratedAudio.id == body.audio_id, GeneratedAudio.user_id == user_id).first()
    if not audio:
        raise HTTPException(status_code=404, detail="Audio asset not found")
    job = RenderingJob(user_id=user_id, project_id=audio.project_id, job_type="audio_edit", status="queued", input_payload=body.model_dump(mode="json"))
    db.add(job)
    db.commit()
    db.refresh(job)
    task = process_audio_job.delay(str(job.id))
    job.celery_task_id = task.id
    db.commit()
    return {"job_id": str(job.id), "status": job.status}


@router.post("/subtitles/generate/{audio_id}")
def enqueue_subtitles(audio_id: UUID, language: str = "en", user_id: UUID = Depends(get_current_user_id), db: Session = Depends(get_db)):
    audio = db.query(GeneratedAudio).filter(GeneratedAudio.id == audio_id, GeneratedAudio.user_id == user_id).first()
    if not audio:
        raise HTTPException(status_code=404, detail="Audio asset not found")
    job = RenderingJob(user_id=user_id, project_id=audio.project_id, job_type="subtitle_gen", status="queued", input_payload={"audio_id": str(audio_id), "language": language})
    db.add(job)
    db.commit()
    db.refresh(job)
    task = generate_subtitles_job.delay(str(job.id))
    job.celery_task_id = task.id
    db.commit()
    return {"job_id": str(job.id), "status": job.status}
