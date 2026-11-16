import uuid
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from supabase import create_client
from app.api.deps import get_current_user_id, get_decrypted_provider_credential
from app.core.config import get_settings
from app.database.session import get_db
from app.models.models import EditingProject, GeneratedImage, RenderingJob
from app.providers.visual_adapters import VisualGenerationAdapter
from app.schemas.schemas import BlenderRenderRequest, VideoRenderRequest, VisualGenerateRequest
from app.workers.tasks import render_blender_3d_job, render_final_video_job

router = APIRouter(prefix="/api/media", tags=["Visuals, 2D/3D Animation & Video"])


@router.post("/visuals/generate")
async def generate_visual_asset(body: VisualGenerateRequest, user_id: UUID = Depends(get_current_user_id), db: Session = Depends(get_db)):
    cred, api_key = get_decrypted_provider_credential(db, user_id, body.provider_slug)
    img_bytes = await VisualGenerationAdapter().generate_image(body.provider_slug, api_key, cred.selected_model, body.prompt, body.width, body.height)
    settings = get_settings()
    sb = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
    img_id = uuid.uuid4()
    storage_path = f"{user_id}/images/{img_id}.png"
    sb.storage.from_("neuroflow-media").upload(storage_path, img_bytes, {"content-type": "image/png", "upsert": "true"})
    signed_url = sb.storage.from_("neuroflow-media").create_signed_url(storage_path, 3600)["signedURL"]

    db.add(GeneratedImage(
        id=img_id, user_id=user_id, project_id=body.project_id, provider_slug=body.provider_slug,
        prompt=body.prompt, storage_path=storage_path, public_url=signed_url,
        width=body.width, height=body.height, asset_kind=body.asset_kind,
    ))
    db.commit()
    return {"image_id": str(img_id), "url": signed_url, "storage_path": storage_path}


@router.post("/3d/render")
def enqueue_3d_render(body: BlenderRenderRequest, user_id: UUID = Depends(get_current_user_id), db: Session = Depends(get_db)):
    job = RenderingJob(user_id=user_id, project_id=body.project_id, job_type="blender_3d", status="queued", input_payload=body.model_dump(mode="json"))
    db.add(job)
    db.commit()
    db.refresh(job)
    task = render_blender_3d_job.delay(str(job.id))
    job.celery_task_id = task.id
    db.commit()
    return {"job_id": str(job.id), "status": job.status}


@router.post("/video/render")
def enqueue_final_video_render(body: VideoRenderRequest, user_id: UUID = Depends(get_current_user_id), db: Session = Depends(get_db)):
    editing = db.query(EditingProject).filter(EditingProject.project_id == body.project_id, EditingProject.user_id == user_id).first()
    if not editing:
        db.add(EditingProject(user_id=user_id, project_id=body.project_id, timeline_state={"clips": body.timeline_clips}))
    else:
        editing.timeline_state = {"clips": body.timeline_clips}

    job = RenderingJob(user_id=user_id, project_id=body.project_id, job_type="video_render", status="queued", input_payload=body.model_dump(mode="json"))
    db.add(job)
    db.commit()
    db.refresh(job)
    task = render_final_video_job.delay(str(job.id))
    job.celery_task_id = task.id
    db.commit()
    return {"job_id": str(job.id), "status": job.status}


@router.get("/jobs")
def list_jobs(user_id: UUID = Depends(get_current_user_id), db: Session = Depends(get_db)):
    jobs = db.query(RenderingJob).filter(RenderingJob.user_id == user_id).order_by(RenderingJob.created_at.desc()).limit(30).all()
    return [
        {"id": str(j.id), "project_id": str(j.project_id) if j.project_id else None, "job_type": j.job_type, "status": j.status, "progress_percent": j.progress_percent, "output_payload": j.output_payload, "error_message": j.error_message, "created_at": j.created_at.isoformat()}
        for j in jobs
    ]


@router.post("/jobs/{job_id}/cancel")
def cancel_job(job_id: UUID, user_id: UUID = Depends(get_current_user_id), db: Session = Depends(get_db)):
    job = db.query(RenderingJob).filter(RenderingJob.id == job_id, RenderingJob.user_id == user_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Render job not found")
    job.status = "cancelled"
    db.commit()
    return {"job_id": str(job.id), "status": "cancelled"}
