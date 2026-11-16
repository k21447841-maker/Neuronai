CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE OR REPLACE FUNCTION public.set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TABLE public.profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT NOT NULL UNIQUE,
    full_name TEXT,
    avatar_url TEXT,
    role TEXT NOT NULL DEFAULT 'user' CHECK (role IN ('user', 'admin')),
    plan_tier TEXT NOT NULL DEFAULT 'starter',
    storage_quota_bytes BIGINT NOT NULL DEFAULT 5368709120,
    storage_used_bytes BIGINT NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.profiles (id, email, full_name, avatar_url)
    VALUES (NEW.id, NEW.email, COALESCE(NEW.raw_user_meta_data->>'full_name', ''), COALESCE(NEW.raw_user_meta_data->>'avatar_url', ''));
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created AFTER INSERT ON auth.users FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

CREATE TABLE public.ai_providers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    slug TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL,
    category TEXT NOT NULL CHECK (category IN ('llm', 'voice', 'visual', 'transcription')),
    default_model TEXT NOT NULL,
    available_models JSONB NOT NULL DEFAULT '[]'::jsonb,
    supports_multimodal BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

INSERT INTO public.ai_providers (slug, display_name, category, default_model, available_models, supports_multimodal) VALUES
('claude', 'Anthropic Claude', 'llm', 'claude-3-7-sonnet-20250219', '["claude-3-7-sonnet-20250219","claude-3-5-haiku-20241022"]'::jsonb, TRUE),
('deepseek', 'DeepSeek', 'llm', 'deepseek-chat', '["deepseek-chat","deepseek-reasoner"]'::jsonb, FALSE),
('gemini', 'Google Gemini', 'llm', 'gemini-2.5-pro', '["gemini-2.5-pro","gemini-2.5-flash"]'::jsonb, TRUE),
('elevenlabs', 'ElevenLabs Voice', 'voice', 'eleven_multilingual_v2', '["eleven_multilingual_v2","eleven_turbo_v2_5"]'::jsonb, FALSE),
('openai_images', 'OpenAI Visual / DALL-E', 'visual', 'gpt-image-1', '["gpt-image-1","dall-e-3"]'::jsonb, FALSE),
('stability', 'Stability AI', 'visual', 'sd3.5-large', '["sd3.5-large","sd3.5-medium"]'::jsonb, FALSE),
('runway', 'Runway Gen Video', 'visual', 'gen4_turbo', '["gen4_turbo"]'::jsonb, TRUE)
ON CONFLICT (slug) DO NOTHING;

CREATE TABLE public.api_credentials (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    provider_slug TEXT NOT NULL REFERENCES public.ai_providers(slug) ON DELETE CASCADE,
    encrypted_api_key TEXT NOT NULL,
    key_hint TEXT NOT NULL,
    selected_model TEXT NOT NULL,
    is_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    connection_status TEXT NOT NULL DEFAULT 'unverified' CHECK (connection_status IN ('unverified', 'connected', 'error')),
    last_error TEXT,
    timeout_seconds INTEGER NOT NULL DEFAULT 60,
    max_retries INTEGER NOT NULL DEFAULT 2,
    task_routing JSONB NOT NULL DEFAULT '{}'::jsonb,
    last_checked_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(user_id, provider_slug)
);

CREATE TABLE public.projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    topic TEXT NOT NULL,
    niche TEXT NOT NULL DEFAULT 'technology',
    format TEXT NOT NULL DEFAULT 'long_form' CHECK (format IN ('shorts', 'long_form', 'square')),
    aspect_ratio TEXT NOT NULL DEFAULT '16:9' CHECK (aspect_ratio IN ('9:16', '16:9', '1:1')),
    target_duration_seconds INTEGER NOT NULL DEFAULT 180,
    language TEXT NOT NULL DEFAULT 'en',
    status TEXT NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'scripting', 'assets', 'rendering', 'ready', 'scheduled', 'published', 'failed')),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE public.scripts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
    provider_slug TEXT NOT NULL,
    model_used TEXT NOT NULL,
    tone TEXT NOT NULL DEFAULT 'engaging',
    storytelling_style TEXT NOT NULL DEFAULT 'documentary',
    hook TEXT NOT NULL DEFAULT '',
    introduction TEXT NOT NULL DEFAULT '',
    body TEXT NOT NULL DEFAULT '',
    ending TEXT NOT NULL DEFAULT '',
    call_to_action TEXT NOT NULL DEFAULT '',
    full_text TEXT NOT NULL DEFAULT '',
    current_version INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE public.script_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    script_id UUID NOT NULL REFERENCES public.scripts(id) ON DELETE CASCADE,
    version_number INTEGER NOT NULL,
    content_snapshot JSONB NOT NULL,
    change_note TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE public.scenes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
    script_id UUID REFERENCES public.scripts(id) ON DELETE SET NULL,
    scene_number INTEGER NOT NULL,
    narration TEXT NOT NULL,
    estimated_duration_seconds NUMERIC(8,2) NOT NULL DEFAULT 5.0,
    visual_description TEXT NOT NULL DEFAULT '',
    camera_movement TEXT NOT NULL DEFAULT 'slow_zoom_in',
    character_description TEXT NOT NULL DEFAULT '',
    background_description TEXT NOT NULL DEFAULT '',
    animation_instructions JSONB NOT NULL DEFAULT '{}'::jsonb,
    sound_effects_cue TEXT NOT NULL DEFAULT '',
    subtitle_text TEXT NOT NULL DEFAULT '',
    animation_mode TEXT NOT NULL DEFAULT '2d' CHECK (animation_mode IN ('2d', '3d', 'stock', 'ai_video')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE public.generated_images (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    project_id UUID REFERENCES public.projects(id) ON DELETE SET NULL,
    provider_slug TEXT NOT NULL,
    prompt TEXT NOT NULL,
    storage_path TEXT NOT NULL,
    public_url TEXT,
    width INTEGER NOT NULL DEFAULT 1920,
    height INTEGER NOT NULL DEFAULT 1080,
    asset_kind TEXT NOT NULL DEFAULT 'scene_frame' CHECK (asset_kind IN ('scene_frame', 'character_ref', 'background', 'thumbnail')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE public.generated_videos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    project_id UUID REFERENCES public.projects(id) ON DELETE SET NULL,
    provider_slug TEXT NOT NULL,
    storage_path TEXT NOT NULL,
    public_url TEXT,
    duration_seconds NUMERIC(10,2) NOT NULL DEFAULT 0,
    resolution TEXT NOT NULL DEFAULT '1920x1080',
    fps INTEGER NOT NULL DEFAULT 30,
    file_size_bytes BIGINT NOT NULL DEFAULT 0,
    video_kind TEXT NOT NULL DEFAULT 'final_render' CHECK (video_kind IN ('scene_2d', 'scene_3d', 'ai_clip', 'final_render')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE public.generated_audio (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    project_id UUID REFERENCES public.projects(id) ON DELETE SET NULL,
    scene_id UUID REFERENCES public.scenes(id) ON DELETE SET NULL,
    provider_slug TEXT NOT NULL DEFAULT 'elevenlabs',
    voice_id TEXT,
    voice_name TEXT,
    storage_path TEXT NOT NULL,
    processed_storage_path TEXT,
    duration_seconds NUMERIC(10,2) NOT NULL DEFAULT 0,
    silence_removed_seconds NUMERIC(10,2) NOT NULL DEFAULT 0,
    settings JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE public.scene_assets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    scene_id UUID NOT NULL REFERENCES public.scenes(id) ON DELETE CASCADE,
    image_id UUID REFERENCES public.generated_images(id) ON DELETE SET NULL,
    video_id UUID REFERENCES public.generated_videos(id) ON DELETE SET NULL,
    audio_id UUID REFERENCES public.generated_audio(id) ON DELETE SET NULL,
    asset_role TEXT NOT NULL DEFAULT 'primary_visual',
    sort_order INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE public.subtitles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
    language TEXT NOT NULL DEFAULT 'en',
    segments JSONB NOT NULL DEFAULT '[]'::jsonb,
    style_config JSONB NOT NULL DEFAULT '{"font":"Inter","size":48,"color":"#FFFFFF","highlight":"#8B5CF6","position":"bottom"}'::jsonb,
    srt_storage_path TEXT,
    vtt_storage_path TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE public.editing_projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
    timeline_state JSONB NOT NULL DEFAULT '{"tracks":{"video":[],"audio":[],"subtitles":[]},"transitions":[]}'::jsonb,
    export_preset JSONB NOT NULL DEFAULT '{"resolution":"1080p","aspect_ratio":"16:9","fps":30,"bitrate":"8M"}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(project_id)
);

CREATE TABLE public.rendering_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    project_id UUID REFERENCES public.projects(id) ON DELETE SET NULL,
    celery_task_id TEXT,
    idempotency_key TEXT UNIQUE,
    job_type TEXT NOT NULL CHECK (job_type IN ('audio_edit', 'animation_2d', 'blender_3d', 'video_render', 'subtitle_gen', 'automation_step')),
    status TEXT NOT NULL DEFAULT 'queued' CHECK (status IN ('queued', 'running', 'completed', 'failed', 'cancelled')),
    progress_percent INTEGER NOT NULL DEFAULT 0 CHECK (progress_percent BETWEEN 0 AND 100),
    input_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    output_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    logs TEXT NOT NULL DEFAULT '',
    error_message TEXT,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE public.connected_channels (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    youtube_channel_id TEXT NOT NULL,
    channel_title TEXT NOT NULL,
    channel_handle TEXT,
    thumbnail_url TEXT,
    subscriber_count BIGINT DEFAULT 0,
    video_count BIGINT DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'expired', 'disconnected', 'error')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(user_id, youtube_channel_id)
);

CREATE TABLE public.oauth_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    channel_id UUID NOT NULL REFERENCES public.connected_channels(id) ON DELETE CASCADE,
    provider TEXT NOT NULL DEFAULT 'google_youtube',
    encrypted_access_token TEXT NOT NULL,
    encrypted_refresh_token TEXT,
    scopes TEXT NOT NULL,
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(channel_id)
);

CREATE TABLE public.automation_workflows (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    channel_id UUID REFERENCES public.connected_channels(id) ON DELETE SET NULL,
    niche TEXT NOT NULL DEFAULT 'technology',
    video_format TEXT NOT NULL DEFAULT 'shorts' CHECK (video_format IN ('shorts', 'long_form')),
    schedule_cron TEXT NOT NULL DEFAULT '0 14 * * *',
    approval_mode TEXT NOT NULL DEFAULT 'manual' CHECK (approval_mode IN ('manual', 'auto_publish')),
    pipeline_config JSONB NOT NULL DEFAULT '{}'::jsonb,
    status TEXT NOT NULL DEFAULT 'paused' CHECK (status IN ('active', 'paused', 'stopped')),
    last_run_at TIMESTAMPTZ,
    next_run_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE public.automation_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    workflow_id UUID NOT NULL REFERENCES public.automation_workflows(id) ON DELETE CASCADE,
    project_id UUID REFERENCES public.projects(id) ON DELETE SET NULL,
    idempotency_key TEXT NOT NULL UNIQUE,
    current_step TEXT NOT NULL DEFAULT 'research',
    status TEXT NOT NULL DEFAULT 'running' CHECK (status IN ('running', 'awaiting_approval', 'completed', 'failed', 'cancelled')),
    step_results JSONB NOT NULL DEFAULT '{}'::jsonb,
    error_message TEXT,
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

CREATE TABLE public.uploads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
    channel_id UUID NOT NULL REFERENCES public.connected_channels(id) ON DELETE CASCADE,
    video_id UUID REFERENCES public.generated_videos(id) ON DELETE SET NULL,
    thumbnail_image_id UUID REFERENCES public.generated_images(id) ON DELETE SET NULL,
    youtube_video_id TEXT,
    title TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    tags JSONB NOT NULL DEFAULT '[]'::jsonb,
    privacy_status TEXT NOT NULL DEFAULT 'private' CHECK (privacy_status IN ('private', 'unlisted', 'public')),
    is_short BOOLEAN NOT NULL DEFAULT FALSE,
    upload_status TEXT NOT NULL DEFAULT 'pending' CHECK (upload_status IN ('pending', 'uploading', 'uploaded', 'failed')),
    idempotency_key TEXT NOT NULL UNIQUE,
    error_message TEXT,
    published_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE public.scheduled_uploads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    upload_id UUID NOT NULL REFERENCES public.uploads(id) ON DELETE CASCADE,
    scheduled_for TIMESTAMPTZ NOT NULL,
    status TEXT NOT NULL DEFAULT 'scheduled' CHECK (status IN ('scheduled', 'dispatched', 'cancelled', 'failed')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE public.notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    level TEXT NOT NULL DEFAULT 'info' CHECK (level IN ('info', 'success', 'warning', 'error')),
    is_read BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE public.usage_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    provider_slug TEXT NOT NULL,
    operation TEXT NOT NULL,
    units_consumed NUMERIC(12,4) NOT NULL DEFAULT 0,
    unit_type TEXT NOT NULL DEFAULT 'tokens',
    estimated_cost_usd NUMERIC(10,6) NOT NULL DEFAULT 0,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE public.billing_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    plan_tier TEXT NOT NULL,
    amount_usd NUMERIC(10,2) NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_projects_user ON public.projects(user_id, created_at DESC);
CREATE INDEX idx_scripts_project ON public.scripts(project_id);
CREATE INDEX idx_scenes_project_num ON public.scenes(project_id, scene_number);
CREATE INDEX idx_rendering_jobs_user_status ON public.rendering_jobs(user_id, status);
CREATE INDEX idx_uploads_user_status ON public.uploads(user_id, upload_status);
CREATE INDEX idx_usage_logs_user_date ON public.usage_logs(user_id, created_at DESC);

ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ai_providers ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.api_credentials ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.scripts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.script_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.scenes ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.generated_images ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.generated_videos ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.generated_audio ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.scene_assets ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.subtitles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.editing_projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.rendering_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.connected_channels ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.oauth_tokens ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.automation_workflows ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.automation_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.uploads ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.scheduled_uploads ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.notifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.usage_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.billing_records ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users read own profile" ON public.profiles FOR SELECT USING (auth.uid() = id);
CREATE POLICY "Users update own profile" ON public.profiles FOR UPDATE USING (auth.uid() = id);
CREATE POLICY "Authenticated read provider catalog" ON public.ai_providers FOR SELECT TO authenticated USING (TRUE);

DO $$
DECLARE tbl TEXT;
BEGIN
    FOREACH tbl IN ARRAY ARRAY[
        'api_credentials','projects','scripts','script_versions','scenes',
        'generated_images','generated_videos','generated_audio','scene_assets',
        'subtitles','editing_projects','rendering_jobs','connected_channels',
        'automation_workflows','automation_runs','uploads','scheduled_uploads',
        'notifications','usage_logs','billing_records'
    ]
    LOOP
        EXECUTE format('CREATE POLICY "Users manage own %s" ON public.%s FOR ALL USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);', tbl, tbl);
    END LOOP;
END $$;

CREATE POLICY "No direct client access to oauth_tokens" ON public.oauth_tokens FOR ALL USING (FALSE);
