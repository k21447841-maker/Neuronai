from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from uuid import UUID
from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    title: str = Field(min_length=2, max_length=160)
    topic: str = Field(min_length=2, max_length=500)
    niche: str = "technology"
    format: Literal["shorts", "long_form", "square"] = "long_form"
    aspect_ratio: Literal["9:16", "16:9", "1:1"] = "16:9"
    target_duration_seconds: int = Field(default=180, ge=15, le=7200)
    language: str = "en"


class ProviderCredentialUpsert(BaseModel):
    provider_slug: str
    api_key: Optional[str] = None
    selected_model: str
    is_enabled: bool = True
    timeout_seconds: int = Field(default=60, ge=10, le=300)
    max_retries: int = Field(default=2, ge=0, le=5)
    task_routing: Dict[str, Any] = Field(default_factory=dict)


class ScriptGenerateRequest(BaseModel):
    project_id: UUID
    topic: str
    niche: str = "technology"
    language: str = "en"
    target_audience: str = "general tech-savvy viewers"
    duration_seconds: int = Field(default=180, ge=15, le=3600)
    content_format: Literal["shorts", "long_form", "square"] = "long_form"
    tone: str = "engaging"
    storytelling_style: str = "documentary"
    provider_slug: Literal["claude", "deepseek", "gemini"] = "claude"
    creativity: float = Field(default=0.7, ge=0.0, le=1.0)


class ScriptEditSectionRequest(BaseModel):
    script_id: UUID
    action: Literal["rewrite", "expand", "shorten", "change_tone", "improve_hook", "translate"]
    selected_text: str
    target_tone: Optional[str] = None
    target_language: Optional[str] = None
    provider_slug: Literal["claude", "deepseek", "gemini"] = "claude"


class VoiceGenerateRequest(BaseModel):
    project_id: UUID
    scene_id: Optional[UUID] = None
    text: str = Field(min_length=1, max_length=5000)
    voice_id: str
    voice_name: str = ""
    model_id: str = "eleven_multilingual_v2"
    stability: float = Field(default=0.5, ge=0.0, le=1.0)
    similarity_boost: float = Field(default=0.75, ge=0.0, le=1.0)
    style: float = Field(default=0.0, ge=0.0, le=1.0)
    speed: float = Field(default=1.0, ge=0.7, le=1.2)


class AudioEditRequest(BaseModel):
    audio_id: UUID
    silence_threshold_db: float = Field(default=-35.0, ge=-60.0, le=-10.0)
    min_silence_duration: float = Field(default=0.45, ge=0.15, le=3.0)
    retain_pause_seconds: float = Field(default=0.18, ge=0.0, le=1.0)
    normalize_loudness: bool = True
    noise_reduction: bool = True
    fade_in_seconds: float = Field(default=0.1, ge=0.0, le=3.0)
    fade_out_seconds: float = Field(default=0.25, ge=0.0, le=5.0)
    background_music_storage_path: Optional[str] = None
    background_music_volume: float = Field(default=0.15, ge=0.0, le=1.0)


class VisualGenerateRequest(BaseModel):
    project_id: UUID
    scene_id: Optional[UUID] = None
    provider_slug: Literal["openai_images", "stability", "runway"] = "openai_images"
    prompt: str = Field(min_length=3, max_length=2000)
    width: int = 1920
    height: int = 1080
    asset_kind: Literal["scene_frame", "character_ref", "background", "thumbnail"] = "scene_frame"


class BlenderRenderRequest(BaseModel):
    project_id: UUID
    scene_id: Optional[UUID] = None
    scene_preset: Literal["studio_showcase", "orbit_logo", "abstract_tech", "character_stage"] = "studio_showcase"
    title_text: str = "NEUROFLOW"
    duration_seconds: float = Field(default=5.0, ge=1.0, le=30.0)
    resolution_x: int = 1280
    resolution_y: int = 720
    fps: int = 24
    samples: int = Field(default=32, ge=8, le=256)
    camera_motion: Literal["orbit", "dolly_in", "pan"] = "orbit"
    preview_only: bool = True


class VideoRenderRequest(BaseModel):
    project_id: UUID
    aspect_ratio: Literal["9:16", "16:9", "1:1"] = "16:9"
    resolution: Literal["720p", "1080p", "4k"] = "1080p"
    fps: int = 30
    burn_subtitles: bool = True
    watermark_text: Optional[str] = None
    timeline_clips: List[Dict[str, Any]] = Field(default_factory=list)


class YouTubeUploadRequest(BaseModel):
    project_id: UUID
    channel_id: UUID
    video_id: UUID
    thumbnail_image_id: Optional[UUID] = None
    title: str = Field(min_length=2, max_length=100)
    description: str = Field(default="", max_length=5000)
    tags: List[str] = Field(default_factory=list)
    privacy_status: Literal["private", "unlisted", "public"] = "private"
    is_short: bool = False
    scheduled_publish_at: Optional[datetime] = None


class AutomationWorkflowCreate(BaseModel):
    name: str
    channel_id: Optional[UUID] = None
    niche: str = "technology"
    video_format: Literal["shorts", "long_form"] = "shorts"
    schedule_cron: str = "0 14 * * *"
    approval_mode: Literal["manual", "auto_publish"] = "manual"
    pipeline_config: Dict[str, Any] = Field(default_factory=dict)
