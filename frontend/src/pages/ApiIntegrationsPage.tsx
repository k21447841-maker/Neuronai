import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { KeyRound, CheckCircle2, AlertCircle } from "lucide-react";
import { apiFetch } from "../services/api";

export function ApiIntegrationsPage() {
  const qc = useQueryClient();
  const [keys, setKeys] = useState<Record<string, string>>({});
  const [models, setModels] = useState<Record<string, string>>({});
  const [notice, setNotice] = useState<string | null>(null);
  const providers = useQuery({ queryKey: ["providers"], queryFn: () => apiFetch<any[]>("/api/providers") });

  const saveMutation = useMutation({
    mutationFn: (p: any) =>
      apiFetch("/api/providers", {
        method: "PUT",
        body: JSON.stringify({
          provider_slug: p.slug,
          api_key: keys[p.slug] || undefined,
          selected_model: models[p.slug] || p.selected_model,
          is_enabled: true,
        }),
      }),
    onSuccess: (_d, p) => {
      setNotice(`${p.display_name} key saved on phone! Now tap Test Connection.`);
      qc.invalidateQueries({ queryKey: ["providers"] });
    },
  });

  const testMutation = useMutation({
    mutationFn: async (p: any) => {
      if (keys[p.slug]?.trim()) {
        await apiFetch("/api/providers", {
          method: "PUT",
          body: JSON.stringify({
            provider_slug: p.slug,
            api_key: keys[p.slug].trim(),
            selected_model: models[p.slug] || p.selected_model,
            is_enabled: true,
          }),
        });
      }
      return apiFetch(`/api/providers/${p.slug}/test`, { method: "POST" });
    },
    onSuccess: (_d, p) => {
      setNotice(`${p.display_name} connected successfully!`);
      qc.invalidateQueries({ queryKey: ["providers"] });
    },
    onError: () => qc.invalidateQueries({ queryKey: ["providers"] }),
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">AI Provider & API Keys</h1>
        <p className="text-sm text-[#94A3B8]">Keys are saved locally inside your phone storage.</p>
      </div>
      {notice && <div className="rounded-lg border border-[#22C55E]/30 bg-[#22C55E]/10 p-3 text-xs text-[#22C55E]">{notice}</div>}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        {(providers.data || []).map((p) => (
          <div key={p.slug} className="rounded-xl border border-white/10 bg-[#171C2B] p-5 space-y-4">
            <div className="flex items-center justify-between">
              <div><h2 className="text-base font-medium text-white">{p.display_name}</h2><span className="text-xs uppercase text-[#94A3B8]">{p.category}</span></div>
              <span className="flex items-center gap-1 text-xs">
                {p.connection_status === "connected" ? <><CheckCircle2 className="h-4 w-4 text-[#22C55E]" /> Connected</> : <><AlertCircle className="h-4 w-4 text-[#94A3B8]" /> {p.connection_status}</>}
              </span>
            </div>
            <div className="space-y-2">
              <label className="block text-xs text-[#94A3B8]">API Key {p.key_hint ? `(Saved: ${p.key_hint})` : "(Not configured)"}</label>
              <div className="flex items-center gap-2">
                <KeyRound className="h-4 w-4 shrink-0 text-[#8B5CF6]" />
                <input type="password" placeholder="Paste your API key..." value={keys[p.slug] || ""} onChange={(e) => setKeys({ ...keys, [p.slug]: e.target.value })} className="w-full rounded-lg border border-white/10 bg-[#111522] px-3 py-2 text-sm text-white" />
              </div>
            </div>
            <div>
              <label className="mb-1 block text-xs text-[#94A3B8]">Model</label>
              <select value={models[p.slug] || p.selected_model} onChange={(e) => setModels({ ...models, [p.slug]: e.target.value })} className="w-full rounded-lg border border-white/10 bg-[#111522] px-3 py-2 text-sm text-white">
                {(p.available_models || []).map((m: string) => <option key={m} value={m}>{m}</option>)}
              </select>
            </div>
            {p.last_error && <p className="text-xs text-[#EF4444] break-words">{p.last_error}</p>}
            <div className="flex flex-wrap gap-2">
              <button onClick={() => saveMutation.mutate(p)} disabled={saveMutation.isPending} className="rounded-lg bg-[#8B5CF6] px-4 py-2 text-xs font-medium text-white">Save Config</button>
              <button onClick={() => testMutation.mutate(p)} disabled={(!p.configured && !keys[p.slug]) || testMutation.isPending} className="rounded-lg border border-white/10 bg-[#111522] px-4 py-2 text-xs font-medium text-white disabled:opacity-40">
                {testMutation.isPending ? "Testing..." : "Test Connection"}
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
