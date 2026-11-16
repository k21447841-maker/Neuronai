import { supabase } from "../lib/supabase";
import { localApiHandler } from "./localEngine";

export function getApiBase(): string {
  const custom = localStorage.getItem("neuroflow_custom_backend_url") || "";
  const envUrl = (import.meta.env.VITE_API_BASE_URL as string) || "";
  const chosen = (custom || envUrl).trim();
  if (!chosen || chosen.includes("localhost") || chosen.includes("127.0.0.1")) {
    return "";
  }
  return chosen.replace(/\/$/, "");
}

export async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  const base = getApiBase();
  if (!base) {
    return localApiHandler<T>(path, options);
  }

  const { data } = await supabase.auth.getSession();
  const token = data.session?.access_token;

  const res = await fetch(`${base}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(options.headers || {}),
    },
  });

  const contentType = res.headers.get("content-type") || "";
  if (!res.ok) {
    if (contentType.includes("application/json")) {
      const errBody = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(errBody.detail || `API request failed (${res.status})`);
    }
    throw new Error(`Server returned ${res.status} (${res.statusText})`);
  }
  if (!contentType.includes("application/json")) {
    throw new Error("Backend did not return valid JSON. Check your Backend URL in Settings.");
  }
  return res.json() as Promise<T>;
}
