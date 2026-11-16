export type ProjectFormat = "shorts" | "long_form" | "square";
export type AspectRatio = "9:16" | "16:9" | "1:1";
export type ProjectStatus =
  | "draft" | "scripting" | "assets" | "rendering"
  | "ready" | "scheduled" | "published" | "failed";

export interface Project {
  id: string;
  title: string;
  topic: string;
  niche: string;
  format: ProjectFormat;
  aspect_ratio: AspectRatio;
  target_duration_seconds: number;
  language: string;
  status: ProjectStatus;
  created_at: string;
}

export interface AIProviderStatus {
  slug: string;
  display_name: string;
  category: "llm" | "voice" | "visual" | "transcription";
  default_model: string;
  available_models: string[];
  supports_multimodal: boolean;
  configured: boolean;
  key_hint: string | null;
  selected_model: string;
  is_enabled: boolean;
  connection_status: "unconfigured" | "unverified" | "connected" | "error";
  last_error: string | null;
  timeout_seconds: number;
  max_retries: number;
}
