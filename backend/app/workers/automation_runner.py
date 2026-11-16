import asyncio
import json
import os
import uuid
from datetime import datetime, timezone
from uuid import UUID
from supabase import create_client
from app.core.config import get_settings
from app.core.security import decrypt_secret
from app.database.session import SessionLocal
from app.models.models import (
    APICredential, AutomationRun, AutomationWorkflow,
    GeneratedVideo, OAuthToken, Project, Scene, Script, Upload
)
from app.providers.elevenlabs_adapter import ElevenLabsAdapter
from app.providers.llm_adapters import get_llm_provider
from app.providers.visual_adapters import VisualGenerationAdapter
from app.audio.processor import process_voice_audio
from app.video.subtitles import export_srt, transcribe_audio_with_whisper
from app.video.renderer import RESOLUTION_MAP, assemble_final_video, render_image_to_2d_animated_clip
from app.youtube.service import credentials_from_encrypted_row, resumable_upload_video
from app.workers.celery_app import celery_app

settings = get_settings()
supabase_admin = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)


def _get_api_key(db, user_id: UUID, provider_slug: str) -> tuple[APICredential, str]:
    cred = db.query(APICredential).filter(
        APICredential.user_id == user_id,
        APICredential.provider_slug == provider_slug,
        APICredential.is_enabled == True,
    ).first()
    if not cred:
        raise ValueError(f"Required provider '{provider_slug}' is not configured or disabled.")
    return cred, decrypt_secret(cred.encrypted_api_key)


@celery_app.task(bind=True, max_retries=2)
def run_automation_pipeline(self, workflow_id: str, topic: str, idempotency_key: str):
    db = SessionLocal()
    wf = db.query(AutomationWorkflow).filter(AutomationWorkflow.id == UUID(workflow_id)).first()
    if not wf:
        db.close()
        return

    existing_run = db.query(AutomationRun).filter(AutomationRun.idempotency_key == idempotency_key).first()
    if existing_run and existing_run.status in ("completed", "awaiting_approval"):
        db.close()
        return

    run = existing_run or AutomationRun(
        user_id=wf.user_id, workflow_id=wf.id, idempotency_key=idempotency_key,
        current_step="scripting", status="running", step_results={},
    )
    if not existing_run:
        db.add(run)
        db.commit()
        db.refresh(run)

    work_dir = os.path.join(settings.MEDIA_WORK_DIR, f"auto_{run.id}")
    os.makedirs(work_dir, exist_ok=True)

    try:
        cfg = wf.pipeline_config or {}
        llm_slug = cfg.get("llm_provider", "claude")
        visual_slug = cfg.get("visual_provider", "openai_images")
        voice_id = cfg.get("voice_id")
        if not voice_id:
            raise ValueError("Automation pipeline_config must include a valid ElevenLabs 'voice_id'.")

        aspect = "9:16" if wf.video_format == "shorts" else "16:9"
        duration = 55 if wf.video_format == "shorts" else 180

        project = Project(
            user_id=wf.user_id, title=f"[Auto] {topic[:80]}", topic=topic, niche=wf.niche,
            format=wf.video_format, aspect_ratio=aspect, target_duration_seconds=duration, status="scripting",
        )
        db.add(project)
        db.flush()
        run.project_id = project.id
        run.current_step = "script_generation"
        db.commit()

        llm_cred, llm_key = _get_api_key(db, wf.user_id, llm_slug)
        llm_resp = asyncio.run(
            get_llm_provider(llm_slug).generate_text(
                api_key=llm_key, model=llm_cred.selected_model,
                system_prompt="Return JSON ONLY with keys: hook, introduction, body, ending, call_to_action, title, description, tags, scenes (array with scene_number, narration, estimated_duration_seconds, visual_description, camera_movement).",
                user_prompt=f"Create a {wf.video_format} YouTube video about '{topic}' in niche '{wf.niche}'.",
            )
        )
        parsed = json.loads(llm_resp.content.strip().removeprefix("```json").removeprefix("```").removesuffix("```"))
        full_narration = "\n".join(sc.get("narration", "") for sc in parsed.get("scenes", [])) or parsed.get("body", "")
        script = Script(
            user_id=wf.user_id, project_id=project.id, provider_slug=llm_slug, model_used=llm_resp.model,
            hook=parsed.get("hook", ""), introduction=parsed.get("introduction", ""),
            body=parsed.get("body", ""), ending=parsed.get("ending", ""),
            call_to_action=parsed.get("call_to_action", ""), full_text=full_narration,
        )
        db.add(script)
        db.flush()

        run.current_step = "visual_generation"
        db.commit()
        vis_cred, vis_key = _get_api_key(db, wf.user_id, visual_slug)
        vis_adapter = VisualGenerationAdapter()
        w, h = RESOLUTION_MAP[(aspect, "1080p")]

        clip_paths = []
        for idx, sc in enumerate(parsed.get("scenes", [])[:8], start=1):
            scene_row = Scene(
                user_id=wf.user_id, project_id=project.id, script_id=script.id, scene_number=idx,
                narration=sc.get("narration", ""), estimated_duration_seconds=sc.get("estimated_duration_seconds", 5.0),
                visual_description=sc.get("visual_description", topic), camera_movement=sc.get("camera_movement", "slow_zoom_in"),
            )
            db.add(scene_row)
            img_bytes = asyncio.run(vis_adapter.generate_image(visual_slug, vis_key, vis_cred.selected_model, scene_row.visual_description, w, h))
            img_local = os.path.join(work_dir, f"scene_{idx}.png")
            open(img_local, "wb").write(img_bytes)
            clip_out = os.path.join(work_dir, f"scene_{idx}.mp4")
            render_image_to_2d_animated_clip(img_local, clip_out, float(scene_row.estimated_duration_seconds), w, h, 30, scene_row.camera_movement)
            clip_paths.append(clip_out)

        run.current_step = "voice_and_audio"
        db.commit()
        _, el_key = _get_api_key(db, wf.user_id, "elevenlabs")
        raw_audio = asyncio.run(ElevenLabsAdapter().synthesize(el_key, voice_id, full_narration))
        raw_mp3, clean_mp3 = os.path.join(work_dir, "raw.mp3"), os.path.join(work_dir, "clean.mp3")
        open(raw_mp3, "wb").write(raw_audio)
        new_dur, removed_dur, _ = process_voice_audio(raw_mp3, clean_mp3)

        run.current_step = "subtitles"
        db.commit()
        srt_path = os.path.join(work_dir, "captions.srt")
        open(srt_path, "w", encoding="utf-8").write(export_srt(transcribe_audio_with_whisper(clean_mp3)))

        run.current_step = "final_render"
        db.commit()
        final_mp4 = os.path.join(work_dir, "final.mp4")
        assemble_final_video(clip_paths, clean_mp3, srt_path, final_mp4, aspect_ratio=aspect, resolution="1080p")
        if not os.path.exists(final_mp4) or os.path.getsize(final_mp4) < 10_000:
            raise RuntimeError("Quality check failed: rendered video file is missing or corrupt.")

        remote_vid = f"{wf.user_id}/renders/auto_{run.id}.mp4"
        with open(final_mp4, "rb") as f:
            supabase_admin.storage.from_("neuroflow-media").upload(remote_vid, f, {"content-type": "video/mp4", "upsert": "true"})

        vid_row = GeneratedVideo(
            user_id=wf.user_id, project_id=project.id, provider_slug="ffmpeg", storage_path=remote_vid,
            duration_seconds=new_dur, resolution=f"{w}x{h}", file_size_bytes=os.path.getsize(final_mp4), video_kind="final_render",
        )
        db.add(vid_row)
        db.flush()

        if wf.approval_mode == "manual" or not wf.channel_id:
            project.status = "ready"
            run.current_step = "awaiting_approval"
            run.status = "awaiting_approval"
            run.step_results = {"video_id": str(vid_row.id), "silence_removed_s": removed_dur}
            db.commit()
            return

        run.current_step = "youtube_upload"
        db.commit()
        token_row = db.query(OAuthToken).filter(OAuthToken.channel_id == wf.channel_id).first()
        if not token_row:
            raise ValueError("Connected YouTube channel missing OAuth token.")
        creds = credentials_from_encrypted_row(token_row)
        yt_id = resumable_upload_video(
            creds, final_mp4, parsed.get("title", topic)[:100], parsed.get("description", topic),
            parsed.get("tags", []), cfg.get("privacy_status", "private"), wf.video_format == "shorts",
        )
        db.add(Upload(
            id=uuid.uuid4(), user_id=wf.user_id, project_id=project.id, channel_id=wf.channel_id,
            video_id=vid_row.id, youtube_video_id=yt_id, title=parsed.get("title", topic)[:100],
            description=parsed.get("description", topic), tags=parsed.get("tags", []),
            privacy_status=cfg.get("privacy_status", "private"), is_short=(wf.video_format == "shorts"),
            upload_status="uploaded", idempotency_key=f"auto_upload:{run.id}", published_at=datetime.now(timezone.utc),
        ))
        project.status = "published"
        run.current_step = "completed"
        run.status = "completed"
        run.completed_at = datetime.now(timezone.utc)
        run.step_results = {"youtube_video_id": yt_id, "video_id": str(vid_row.id)}
        wf.last_run_at = datetime.now(timezone.utc)
        db.commit()
    except Exception as exc:
        run.status = "failed"
        run.error_message = str(exc)
        db.commit()
    finally:
        db.close()
