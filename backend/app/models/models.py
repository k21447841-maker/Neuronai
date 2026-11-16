import uuid
from datetime import datetime
from sqlalchemy import BigInteger, Boolean, Column, DateTime, ForeignKey, Integer, Numeric, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from app.database.session import Base


class Profile(Base):
    __tablename__ = "profiles"
    id = Column(UUID(as_uuid=True), primary_key=True)
    email = Column(Text, nullable=False, unique=True)
    full_name = Column(Text)
    avatar_url = Column(Text)
    role = Column(Text, nullable=False, default="user")
    plan_tier = Column(Text, nullable=False, default="starter")
    storage_quota_bytes = Column(BigInteger, nullable=False, default=5368709120)
    storage_used_bytes = Column(BigInteger, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class AIProvider(Base):
    __tablename__ = "ai_providers"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug = Column(Text, nullable=False, unique=True)
    display_name = Column(Text, nullable=False)
    category = Column(Text, nullable=False)
    default_model = Column(Text, nullable=False)
    available_models = Column(JSONB, nullable=False, default=list)
    supports_multimodal = Column(Boolean, nullable=False, default=False)
    is_active = Column(Boolean, nullable=False, default=True)


class APICredential(Base):
    __tablename__ = "api_credentials"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    provider_slug = Column(Text, ForeignKey("ai_providers.slug"), nullable=False)
    encrypted_api_key = Column(Text, nullable=False)
    key_hint = Column(Text, nullable=False)
    selected_model = Column(Text, nullable=False)
    is_enabled = Column(Boolean, nullable=False, default=True)
    connection_status = Column(Text, nullable=False, default="unverified")
    last_error = Column(Text)
    timeout_seconds = Column(Integer, nullable=False, default=60)
    max_retries = Column(Integer, nullable=False, default=2)
    task_routing = Column(JSONB, nullable=False, default=dict)
    last_checked_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class Project(Base):
    __tablename__ = "projects"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    title = Column(Text, nullable=False)
    topic = Column(Text, nullable=False)
    niche = Column(Text, nullable=False, default="technology")
    format = Column(Text, nullable=False, default="long_form")
    aspect_ratio = Column(Text, nullable=False, default="16:9")
    target_duration_seconds = Column(Integer, nullable=False, default=180)
    language = Column(Text, nullable=False, default="en")
    status = Column(Text, nullable=False, default="draft")
    metadata_json = Column("metadata", JSONB, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class Script(Base):
    __tablename__ = "scripts"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    provider_slug = Column(Text, nullable=False)
    model_used = Column(Text, nullable=False)
    tone = Column(Text, nullable=False, default="engaging")
    storytelling_style = Column(Text, nullable=False, default="documentary")
    hook = Column(Text, nullable=False, default="")
    introduction = Column(Text, nullable=False, default="")
    body = Column(Text, nullable=False, default="")
    ending = Column(Text, nullable=False, default="")
    call_to_action = Column(Text, nullable=False, default="")
    full_text = Column(Text, nullable=False, default="")
    current_version = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class ScriptVersion(Base):
    __tablename__ = "script_versions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    script_id = Column(UUID(as_uuid=True), ForeignKey("scripts.id", ondelete="CASCADE"), nullable=False)
    version_number = Column(Integer, nullable=False)
    content_snapshot = Column(JSONB, nullable=False)
    change_note = Column(Text)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class Scene(Base):
    __tablename__ = "scenes"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    script_id = Column(UUID(as_uuid=True), ForeignKey("scripts.id", ondelete="SET NULL"))
    scene_number = Column(Integer, nullable=False)
    narration = Column(Text, nullable=False)
    estimated_duration_seconds = Column(Numeric(8, 2), nullable=False, default=5.0)
    visual_description = Column(Text, nullable=False, default="")
    camera_movement = Column(Text, nullable=False, default="slow_zoom_in")
    character_description = Column(Text, nullable=False, default="")
    background_description = Column(Text, nullable=False, default="")
    animation_instructions = Column(JSONB, nullable=False, default=dict)
    sound_effects_cue = Column(Text, nullable=False, default="")
    subtitle_text = Column(Text, nullable=False, default="")
    animation_mode = Column(Text, nullable=False, default="2d")
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class GeneratedImage(Base):
    __tablename__ = "generated_images"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="SET NULL"))
    provider_slug = Column(Text, nullable=False)
    prompt = Column(Text, nullable=False)
    storage_path = Column(Text, nullable=False)
    public_url = Column(Text)
    width = Column(Integer, nullable=False, default=1920)
    height = Column(Integer, nullable=False, default=1080)
    asset_kind = Column(Text, nullable=False, default="scene_frame")
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class GeneratedVideo(Base):
    __tablename__ = "generated_videos"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="SET NULL"))
    provider_slug = Column(Text, nullable=False)
    storage_path = Column(Text, nullable=False)
    public_url = Column(Text)
    duration_seconds = Column(Numeric(10, 2), nullable=False, default=0)
    resolution = Column(Text, nullable=False, default="1920x1080")
    fps = Column(Integer, nullable=False, default=30)
    file_size_bytes = Column(BigInteger, nullable=False, default=0)
    video_kind = Column(Text, nullable=False, default="final_render")
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class GeneratedAudio(Base):
    __tablename__ = "generated_audio"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="SET NULL"))
    scene_id = Column(UUID(as_uuid=True), ForeignKey("scenes.id", ondelete="SET NULL"))
    provider_slug = Column(Text, nullable=False, default="elevenlabs")
    voice_id = Column(Text)
    voice_name = Column(Text)
    storage_path = Column(Text, nullable=False)
    processed_storage_path = Column(Text)
    duration_seconds = Column(Numeric(10, 2), nullable=False, default=0)
    silence_removed_seconds = Column(Numeric(10, 2), nullable=False, default=0)
    settings = Column(JSONB, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class Subtitle(Base):
    __tablename__ = "subtitles"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    language = Column(Text, nullable=False, default="en")
    segments = Column(JSONB, nullable=False, default=list)
    style_config = Column(JSONB, nullable=False, default=dict)
    srt_storage_path = Column(Text)
    vtt_storage_path = Column(Text)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class EditingProject(Base):
    __tablename__ = "editing_projects"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, unique=True)
    timeline_state = Column(JSONB, nullable=False, default=dict)
    export_preset = Column(JSONB, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class RenderingJob(Base):
    __tablename__ = "rendering_jobs"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="SET NULL"))
    celery_task_id = Column(Text)
    idempotency_key = Column(Text, unique=True)
    job_type = Column(Text, nullable=False)
    status = Column(Text, nullable=False, default="queued")
    progress_percent = Column(Integer, nullable=False, default=0)
    input_payload = Column(JSONB, nullable=False, default=dict)
    output_payload = Column(JSONB, nullable=False, default=dict)
    logs = Column(Text, nullable=False, default="")
    error_message = Column(Text)
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class ConnectedChannel(Base):
    __tablename__ = "connected_channels"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    youtube_channel_id = Column(Text, nullable=False)
    channel_title = Column(Text, nullable=False)
    channel_handle = Column(Text)
    thumbnail_url = Column(Text)
    subscriber_count = Column(BigInteger, default=0)
    video_count = Column(BigInteger, default=0)
    status = Column(Text, nullable=False, default="active")
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class OAuthToken(Base):
    __tablename__ = "oauth_tokens"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    channel_id = Column(UUID(as_uuid=True), ForeignKey("connected_channels.id", ondelete="CASCADE"), nullable=False, unique=True)
    provider = Column(Text, nullable=False, default="google_youtube")
    encrypted_access_token = Column(Text, nullable=False)
    encrypted_refresh_token = Column(Text)
    scopes = Column(Text, nullable=False)
    expires_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class AutomationWorkflow(Base):
    __tablename__ = "automation_workflows"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    name = Column(Text, nullable=False)
    channel_id = Column(UUID(as_uuid=True), ForeignKey("connected_channels.id", ondelete="SET NULL"))
    niche = Column(Text, nullable=False, default="technology")
    video_format = Column(Text, nullable=False, default="shorts")
    schedule_cron = Column(Text, nullable=False, default="0 14 * * *")
    approval_mode = Column(Text, nullable=False, default="manual")
    pipeline_config = Column(JSONB, nullable=False, default=dict)
    status = Column(Text, nullable=False, default="paused")
    last_run_at = Column(DateTime(timezone=True))
    next_run_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class AutomationRun(Base):
    __tablename__ = "automation_runs"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    workflow_id = Column(UUID(as_uuid=True), ForeignKey("automation_workflows.id", ondelete="CASCADE"), nullable=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="SET NULL"))
    idempotency_key = Column(Text, nullable=False, unique=True)
    current_step = Column(Text, nullable=False, default="research")
    status = Column(Text, nullable=False, default="running")
    step_results = Column(JSONB, nullable=False, default=dict)
    error_message = Column(Text)
    started_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    completed_at = Column(DateTime(timezone=True))


class Upload(Base):
    __tablename__ = "uploads"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    channel_id = Column(UUID(as_uuid=True), ForeignKey("connected_channels.id", ondelete="CASCADE"), nullable=False)
    video_id = Column(UUID(as_uuid=True), ForeignKey("generated_videos.id", ondelete="SET NULL"))
    thumbnail_image_id = Column(UUID(as_uuid=True), ForeignKey("generated_images.id", ondelete="SET NULL"))
    youtube_video_id = Column(Text)
    title = Column(Text, nullable=False)
    description = Column(Text, nullable=False, default="")
    tags = Column(JSONB, nullable=False, default=list)
    privacy_status = Column(Text, nullable=False, default="private")
    is_short = Column(Boolean, nullable=False, default=False)
    upload_status = Column(Text, nullable=False, default="pending")
    idempotency_key = Column(Text, nullable=False, unique=True)
    error_message = Column(Text)
    published_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class ScheduledUpload(Base):
    __tablename__ = "scheduled_uploads"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    upload_id = Column(UUID(as_uuid=True), ForeignKey("uploads.id", ondelete="CASCADE"), nullable=False)
    scheduled_for = Column(DateTime(timezone=True), nullable=False)
    status = Column(Text, nullable=False, default="scheduled")
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class UsageLog(Base):
    __tablename__ = "usage_logs"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    provider_slug = Column(Text, nullable=False)
    operation = Column(Text, nullable=False)
    units_consumed = Column(Numeric(12, 4), nullable=False, default=0)
    unit_type = Column(Text, nullable=False, default="tokens")
    estimated_cost_usd = Column(Numeric(10, 6), nullable=False, default=0)
    metadata_json = Column("metadata", JSONB, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
