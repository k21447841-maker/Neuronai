import json
import os
from datetime import datetime, timezone
from uuid import UUID
import redis
from supabase import create_client
from app.core.config import get_settings
from app.database.session import SessionLocal
from app.models.models import (
    GeneratedAudio, GeneratedImage, GeneratedVideo,
    OAuthToken, RenderingJob, Scene, Subtitle, Upload, ScheduledUpload
)
from app.audio.processor import process_voice_audio
from app.video.renderer import assemble_final_video, render_image_to_2d_animated_clip, RESOLUTION_MAP
from app.video.subtitles import export_srt, export_vtt, transcribe_audio_with_whisper
from app.animation.blender_worker import build_blender_python_script, run_blender_render
from app.youtube.service import credentials_from_encrypted_row, resumable_upload_video
from app.workers.celery_app import celery_app

settings = get_settings()
redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
supabase_admin = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)


def publish_job_event(job_id: str, status: str, progress: int, message: str = "") -> None:
    redis_client.publish(f"job_updates:{job_id}", json.dumps({"job_id": job_id, "status": status, "progress": progress, "message": message}))


def _download_storage_file(bucket: str, storage_path: str, local_path: str) -> str:
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    data = supabase_admin.storage.from_(bucket).download(storage_path)
    with open(local_path, "wb") as f:
        f.write(data)
    return local_path


def _upload_storage_file(bucket: str, storage_path: str, local_path: str, content_type: str) -> str:
    with open(local_path, "rb") as f:
        supabase_admin.storage.from_(bucket).upload(storage_path, f, file_options={"content-type": content_type, "upsert": "true"})
    return supabase_admin.storage.from_(bucket).create_signed_url(storage_path, 3600)["signedURL"]


@celery_app.task(bind=True, max_retries=2)
def process_audio_job(self, job_id: str):
    db = SessionLocal()
    job = db.query(RenderingJob).filter(RenderingJob.id == UUID(job_id)).first()
    if not job:
        db.close()
        return
    try:
        job.status = "running"
        job.started_at = datetime.now(timezone.utc)
        job.progress_percent = 10
        db.commit()
        publish_job_event(job_id, "running", 10, "Downloading source voice audio")

        p = job.input_payload
        audio = db.query(GeneratedAudio).filter(GeneratedAudio.id == UUID(p["audio_id"])).first()
        work_dir = os.path.join(settings.MEDIA_WORK_DIR, job_id)
        in_path = _download_storage_file("neuroflow-media", audio.storage_path, os.path.join(work_dir, "input.mp3"))
        out_path = os.path.join(work_dir, "processed.mp3")

        publish_job_event(job_id, "running", 45, "Running FFmpeg silence & noise pipeline")
        new_dur, removed_dur, silences = process_voice_audio(
            in_path, out_path,
            threshold_db=p.get("silence_threshold_db", -35.0),
            min_silence_duration=p.get("min_silence_duration", 0.45),
            retain_pause_seconds=p.get("retain_pause_seconds", 0.18),
            normalize_loudness=p.get("normalize_loudness", True),
            noise_reduction=p.get("noise_reduction", True),
            fade_in_seconds=p.get("fade_in_seconds", 0.1),
            fade_out_seconds=p.get("fade_out_seconds", 0.25),
        )

        proc_path = f"{audio.user_id}/audio/{audio.id}_processed.mp3"
        signed_url = _upload_storage_file("neuroflow-media", proc_path, out_path, "audio/mpeg")
        audio.processed_storage_path = proc_path
        audio.duration_seconds = new_dur
        audio.silence_removed_seconds = removed_dur

        job.status = "completed"
        job.progress_percent = 100
        job.completed_at = datetime.now(timezone.utc)
        job.output_payload = {"processed_url": signed_url, "duration": new_dur, "removed_seconds": removed_dur, "silences_found": len(silences)}
        db.commit()
        publish_job_event(job_id, "completed", 100, "Audio editing completed")
    except Exception as exc:
        job.status = "failed"
        job.error_message = str(exc)
        db.commit()
        publish_job_event(job_id, "failed", job.progress_percent, str(exc))
    finally:
        db.close()


@celery_app.task(bind=True)
def generate_subtitles_job(self, job_id: str):
    db = SessionLocal()
    job = db.query(RenderingJob).filter(RenderingJob.id == UUID(job_id)).first()
    if not job:
        db.close()
        return
    try:
        job.status = "running"
        job.started_at = datetime.now(timezone.utc)
        db.commit()
        publish_job_event(job_id, "running", 20, "Running Whisper speech recognition")

        p = job.input_payload
        audio = db.query(GeneratedAudio).filter(GeneratedAudio.id == UUID(p["audio_id"])).first()
        src_path = audio.processed_storage_path or audio.storage_path
        work_dir = os.path.join(settings.MEDIA_WORK_DIR, job_id)
        local_audio = _download_storage_file("neuroflow-media", src_path, os.path.join(work_dir, "audio.mp3"))

        segments = transcribe_audio_with_whisper(local_audio, language=p.get("language"))
        srt_local = os.path.join(work_dir, "subtitles.srt")
        vtt_local = os.path.join(work_dir, "subtitles.vtt")
        open(srt_local, "w", encoding="utf-8").write(export_srt(segments))
        open(vtt_local, "w", encoding="utf-8").write(export_vtt(segments))

        srt_remote = f"{job.user_id}/subtitles/{job.project_id}.srt"
        vtt_remote = f"{job.user_id}/subtitles/{job.project_id}.vtt"
        _upload_storage_file("neuroflow-media", srt_remote, srt_local, "text/plain")
        _upload_storage_file("neuroflow-media", vtt_remote, vtt_local, "text/vtt")

        sub = Subtitle(user_id=job.user_id, project_id=job.project_id, language=p.get("language", "en"), segments=segments, srt_storage_path=srt_remote, vtt_storage_path=vtt_remote)
        db.add(sub)
        db.flush()

        job.status = "completed"
        job.progress_percent = 100
        job.completed_at = datetime.now(timezone.utc)
        job.output_payload = {"subtitle_id": str(sub.id), "segment_count": len(segments)}
        db.commit()
        publish_job_event(job_id, "completed", 100, "Subtitles generated")
    except Exception as exc:
        job.status = "failed"
        job.error_message = str(exc)
        db.commit()
        publish_job_event(job_id, "failed", job.progress_percent, str(exc))
    finally:
        db.close()


@celery_app.task(bind=True)
def render_blender_3d_job(self, job_id: str):
    db = SessionLocal()
    job = db.query(RenderingJob).filter(RenderingJob.id == UUID(job_id)).first()
    if not job:
        db.close()
        return
    try:
        job.status = "running"
        job.started_at = datetime.now(timezone.utc)
        db.commit()
        publish_job_event(job_id, "running", 10, "Preparing Blender Python scene")

        p = job.input_payload
        work_dir = os.path.join(settings.MEDIA_WORK_DIR, job_id)
        os.makedirs(work_dir, exist_ok=True)
        out_mp4 = os.path.join(work_dir, "render_3d.mp4")
        py_path = os.path.join(work_dir, "scene.py")
        fps = p.get("fps", 24)
        total_frames = max(24, int(p.get("duration_seconds", 5.0) * fps))

        script_src = build_blender_python_script(
            out_mp4, p.get("scene_preset", "studio_showcase"), p.get("title_text", "NEUROFLOW"),
            p.get("duration_seconds", 5.0), p.get("resolution_x", 1280), p.get("resolution_y", 720),
            fps, p.get("samples", 32), p.get("camera_motion", "orbit"),
        )
        open(py_path, "w", encoding="utf-8").write(script_src)

        def on_prog(frame: int, line: str):
            publish_job_event(job_id, "running", min(95, max(10, int((frame / total_frames) * 85) + 10)), line)

        def is_cancelled() -> bool:
            db.refresh(job)
            return job.status == "cancelled"

        logs = run_blender_render(py_path, on_progress=on_prog, cancel_check=is_cancelled)
        remote_path = f"{job.user_id}/videos/{job_id}_3d.mp4"
        url = _upload_storage_file("neuroflow-media", remote_path, out_mp4, "video/mp4")

        vid = GeneratedVideo(user_id=job.user_id, project_id=job.project_id, provider_slug="blender", storage_path=remote_path, public_url=url, duration_seconds=p.get("duration_seconds", 5.0), resolution=f"{p.get('resolution_x', 1280)}x{p.get('resolution_y', 720)}", fps=fps, file_size_bytes=os.path.getsize(out_mp4), video_kind="scene_3d")
        db.add(vid)
        db.flush()

        job.status = "completed"
        job.progress_percent = 100
        job.logs = logs[-4000:]
        job.completed_at = datetime.now(timezone.utc)
        job.output_payload = {"video_id": str(vid.id), "video_url": url}
        db.commit()
        publish_job_event(job_id, "completed", 100, "3D render complete")
    except Exception as exc:
        job.status = "failed"
        job.error_message = str(exc)
        db.commit()
        publish_job_event(job_id, "failed", job.progress_percent, str(exc))
    finally:
        db.close()


@celery_app.task(bind=True)
def render_final_video_job(self, job_id: str):
    db = SessionLocal()
    job = db.query(RenderingJob).filter(RenderingJob.id == UUID(job_id)).first()
    if not job:
        db.close()
        return
    try:
        job.status = "running"
        job.started_at = datetime.now(timezone.utc)
        db.commit()
        publish_job_event(job_id, "running", 15, "Collecting project assets")

        p = job.input_payload
        work_dir = os.path.join(settings.MEDIA_WORK_DIR, job_id)
        os.makedirs(work_dir, exist_ok=True)
        aspect, res, fps = p.get("aspect_ratio", "16:9"), p.get("resolution", "1080p"), p.get("fps", 30)
        width, height = RESOLUTION_MAP.get((aspect, res), (1920, 1080))

        clip_paths = []
        videos = db.query(GeneratedVideo).filter(GeneratedVideo.project_id == job.project_id, GeneratedVideo.video_kind != "final_render").all()
        for idx, v in enumerate(videos):
            clip_paths.append(_download_storage_file("neuroflow-media", v.storage_path, os.path.join(work_dir, f"vid_{idx}.mp4")))

        if not clip_paths:
            images = db.query(GeneratedImage).filter(GeneratedImage.project_id == job.project_id).all()
            scenes = db.query(Scene).filter(Scene.project_id == job.project_id).order_by(Scene.scene_number).all()
            for idx, img in enumerate(images):
                local_img = _download_storage_file("neuroflow-media", img.storage_path, os.path.join(work_dir, f"img_{idx}.png"))
                dur = float(scenes[idx].estimated_duration_seconds) if idx < len(scenes) else 5.0
                cam = scenes[idx].camera_movement if idx < len(scenes) else "slow_zoom_in"
                clip_out = os.path.join(work_dir, f"anim2d_{idx}.mp4")
                render_image_to_2d_animated_clip(local_img, clip_out, dur, width, height, fps, cam)
                clip_paths.append(clip_out)

        if not clip_paths:
            raise ValueError("No visual clips or scene images exist in this project to render.")

        audio = db.query(GeneratedAudio).filter(GeneratedAudio.project_id == job.project_id).order_by(GeneratedAudio.created_at.desc()).first()
        local_audio = _download_storage_file("neuroflow-media", audio.processed_storage_path or audio.storage_path, os.path.join(work_dir, "narration.mp3")) if audio else None
        local_srt = None
        if p.get("burn_subtitles", True):
            sub = db.query(Subtitle).filter(Subtitle.project_id == job.project_id).order_by(Subtitle.created_at.desc()).first()
            if sub and sub.srt_storage_path:
                local_srt = _download_storage_file("neuroflow-media", sub.srt_storage_path, os.path.join(work_dir, "subs.srt"))

        publish_job_event(job_id, "running", 65, "Encoding final MP4 via FFmpeg")
        final_mp4 = os.path.join(work_dir, "final_output.mp4")
        assemble_final_video(clip_paths, local_audio, local_srt, final_mp4, aspect, res, fps, p.get("watermark_text"))

        remote_path = f"{job.user_id}/renders/{job_id}_final.mp4"
        url = _upload_storage_file("neuroflow-media", remote_path, final_mp4, "video/mp4")
        vid = GeneratedVideo(user_id=job.user_id, project_id=job.project_id, provider_slug="ffmpeg", storage_path=remote_path, public_url=url, resolution=f"{width}x{height}", fps=fps, file_size_bytes=os.path.getsize(final_mp4), video_kind="final_render")
        db.add(vid)
        db.flush()

        job.status = "completed"
        job.progress_percent = 100
        job.completed_at = datetime.now(timezone.utc)
        job.output_payload = {"video_id": str(vid.id), "video_url": url}
        db.commit()
        publish_job_event(job_id, "completed", 100, "Final video render completed")
    except Exception as exc:
        job.status = "failed"
        job.error_message = str(exc)
        db.commit()
        publish_job_event(job_id, "failed", job.progress_percent, str(exc))
    finally:
        db.close()


@celery_app.task(bind=True, max_retries=3)
def youtube_upload_task(self, upload_id: str):
    db = SessionLocal()
    upload = db.query(Upload).filter(Upload.id == UUID(upload_id)).first()
    if not upload or upload.upload_status == "uploaded":
        db.close()
        return
    try:
        upload.upload_status = "uploading"
        db.commit()
        token_row = db.query(OAuthToken).filter(OAuthToken.channel_id == upload.channel_id).first()
        if not token_row:
            raise ValueError("Missing OAuth credentials for selected YouTube channel.")
        creds = credentials_from_encrypted_row(token_row)
        db.commit()

        video = db.query(GeneratedVideo).filter(GeneratedVideo.id == upload.video_id).first()
        work_dir = os.path.join(settings.MEDIA_WORK_DIR, f"yt_{upload_id}")
        local_video = _download_storage_file("neuroflow-media", video.storage_path, os.path.join(work_dir, "upload.mp4"))
        local_thumb = None
        if upload.thumbnail_image_id:
            thumb = db.query(GeneratedImage).filter(GeneratedImage.id == upload.thumbnail_image_id).first()
            if thumb:
                local_thumb = _download_storage_file("neuroflow-media", thumb.storage_path, os.path.join(work_dir, "thumb.png"))

        yt_id = resumable_upload_video(creds, local_video, upload.title, upload.description, upload.tags or [], upload.privacy_status, upload.is_short, thumbnail_path=local_thumb)
        upload.youtube_video_id = yt_id
        upload.upload_status = "uploaded"
        upload.published_at = datetime.now(timezone.utc)
        db.commit()
    except Exception as exc:
        upload.upload_status = "failed"
        upload.error_message = str(exc)
        db.commit()
    finally:
        db.close()


@celery_app.task
def dispatch_due_uploads():
    db = SessionLocal()
    try:
        due = db.query(ScheduledUpload).filter(ScheduledUpload.status == "scheduled", ScheduledUpload.scheduled_for <= datetime.now(timezone.utc)).all()
        for item in due:
            item.status = "dispatched"
            youtube_upload_task.delay(str(item.upload_id))
        db.commit()
    finally:
        db.close()
