import { supabase } from "../lib/supabase";
import { localApiHandler } from "./localEngine";

export function getApiBase(): string {
  return localStorage.getItem("neuroflow_custom_backend_url") || (import.meta.env.VITE_API_BASE_URL as string) || "";
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

  if (!res.ok) {
    const errBody = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(errBody.detail || `API request failed (${res.status})`);
  }
  return res.json() as Promise<T>;
}
