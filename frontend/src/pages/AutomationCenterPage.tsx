import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Play, Pause, Square, Workflow, Zap } from "lucide-react";
import { apiFetch } from "../services/api";

export function AutomationCenterPage() {
  const qc = useQueryClient();
  const [name, setName] = useState("");
  const [niche, setNiche] = useState("Technology");
  const [format, setFormat] = useState<"shorts" | "long_form">("shorts");
  const [approval, setApproval] = useState<"manual" | "auto_publish">("manual");
  const [runTopic, setRunTopic] = useState("");

  const workflows = useQuery({ queryKey: ["workflows"], queryFn: () => apiFetch<any[]>("/api/automation/workflows") });
  const createWf = useMutation({
    mutationFn: () => apiFetch("/api/automation/workflows", { method: "POST", body: JSON.stringify({ name, niche, video_format: format, approval_mode: approval }) }),
    onSuccess: () => { setName(""); qc.invalidateQueries({ queryKey: ["workflows"] }); },
  });
  const setStatus = useMutation({
    mutationFn: ({ id, status }: { id: string; status: string }) => apiFetch(`/api/automation/workflows/${id}/status?status=${status}`, { method: "PATCH" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["workflows"] }),
  });
  const triggerRun = useMutation({
    mutationFn: ({ id, topic }: { id: string; topic: string }) => apiFetch(`/api/automation/workflows/${id}/run?topic=${encodeURIComponent(topic)}`, { method: "POST" }),
  });

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Automation Workflow Engine</h1>
      <div className="grid grid-cols-1 gap-3 rounded-xl border border-white/10 bg-[#171C2B] p-5 md:grid-cols-5">
        <input placeholder="Workflow name" value={name} onChange={(e) => setName(e.target.value)} className="rounded-lg border border-white/10 bg-[#111522] px-3 py-2 text-sm md:col-span-2" />
        <input value={niche} onChange={(e) => setNiche(e.target.value)} className="rounded-lg border border-white/10 bg-[#111522] px-3 py-2 text-sm" />
        <select value={approval} onChange={(e) => setApproval(e.target.value as any)} className="rounded-lg border border-white/10 bg-[#111522] px-3 py-2 text-sm"><option value="manual">Manual Approval</option><option value="auto_publish">Auto-Publish Rule</option></select>
        <button onClick={() => createWf.mutate()} disabled={!name} className="flex items-center justify-center gap-1.5 rounded-lg bg-[#8B5CF6] px-4 py-2 text-sm font-medium text-white disabled:opacity-40"><Workflow className="h-4 w-4" /> Add Rule</button>
      </div>
      <div className="flex gap-2">
        <input placeholder="Topic for manual pipeline run..." value={runTopic} onChange={(e) => setRunTopic(e.target.value)} className="flex-1 rounded-lg border border-white/10 bg-[#171C2B] px-3 py-2 text-sm" />
      </div>
      <div className="space-y-3">
        {(workflows.data || []).map((w) => (
          <div key={w.id} className="flex items-center justify-between rounded-xl border border-white/10 bg-[#171C2B] p-4">
            <div><div className="font-medium text-white">{w.name}</div><div className="text-xs text-[#94A3B8]">{w.niche} • {w.video_format} • {w.approval_mode} • Status: {w.status}</div></div>
            <div className="flex gap-2">
              <button onClick={() => runTopic && triggerRun.mutate({ id: w.id, topic: runTopic })} disabled={!runTopic} title="Run Now" className="rounded bg-[#8B5CF6]/20 p-2 text-[#8B5CF6] disabled:opacity-40"><Zap className="h-4 w-4" /></button>
              <button onClick={() => setStatus.mutate({ id: w.id, status: "active" })} className="rounded bg-[#22C55E]/15 p-2 text-[#22C55E]"><Play className="h-4 w-4" /></button>
              <button onClick={() => setStatus.mutate({ id: w.id, status: "paused" })} className="rounded bg-white/10 p-2 text-white"><Pause className="h-4 w-4" /></button>
              <button onClick={() => setStatus.mutate({ id: w.id, status: "stopped" })} className="rounded bg-[#EF4444]/15 p-2 text-[#EF4444]"><Square className="h-4 w-4" /></button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
