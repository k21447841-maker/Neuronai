import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus, Video, CheckCircle2, Clock, AlertTriangle, Youtube, Mic } from "lucide-react";
import { apiFetch } from "../services/api";
import { useAppStore } from "../stores/appStore";
import { StatusBadge } from "../components/ui/StatusBadge";

export function OverviewPage() {
  const qc = useQueryClient();
  const { activeProjectId, setActiveProjectId } = useAppStore();
  const [title, setTitle] = useState("");
  const [topic, setTopic] = useState("");
  const [format, setFormat] = useState<"long_form" | "shorts">("long_form");

  const overview = useQuery({ queryKey: ["overview"], queryFn: () => apiFetch<any>("/api/analytics/overview") });
  const projects = useQuery({ queryKey: ["projects"], queryFn: () => apiFetch<any[]>("/api/projects") });
  const jobs = useQuery({ queryKey: ["jobs"], queryFn: () => apiFetch<any[]>("/api/media/jobs") });
  const providers = useQuery({ queryKey: ["providers"], queryFn: () => apiFetch<any[]>("/api/providers") });

  const createProject = useMutation({
    mutationFn: () =>
      apiFetch<any>("/api/projects", {
        method: "POST",
        body: JSON.stringify({ title, topic, format, aspect_ratio: format === "shorts" ? "9:16" : "16:9", target_duration_seconds: format === "shorts" ? 55 : 180 }),
      }),
    onSuccess: (res) => { setTitle(""); setTopic(""); setActiveProjectId(res.id); qc.invalidateQueries({ queryKey: ["projects"] }); },
  });

  const s = overview.data;
  const kpis = [
    { label: "Generated Videos", value: s?.total_generated_videos ?? 0, icon: Video },
    { label: "Published Videos", value: s?.total_published_videos ?? 0, icon: CheckCircle2 },
    { label: "Scheduled Videos", value: s?.total_scheduled_videos ?? 0, icon: Clock },
    { label: "Failed Jobs", value: s?.failed_generation_jobs ?? 0, icon: AlertTriangle },
    { label: "Connected Channels", value: s?.connected_channels ?? 0, icon: Youtube },
    { label: "Voice Chars Used", value: s?.voice_characters_used ?? 0, icon: Mic },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Production Overview</h1>
        <p className="text-sm text-[#94A3B8]">Real-time status across AI providers, rendering queues, and channels.</p>
      </div>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-6">
        {kpis.map(({ label, value, icon: Icon }) => (
          <div key={label} className="rounded-xl border border-white/10 bg-[#171C2B] p-4">
            <div className="flex items-center justify-between text-[#94A3B8]"><span className="text-xs">{label}</span><Icon className="h-4 w-4 text-[#8B5CF6]" /></div>
            <div className="mt-2 text-2xl font-semibold text-white">{value}</div>
          </div>
        ))}
      </div>
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="rounded-xl border border-white/10 bg-[#171C2B] p-5 lg:col-span-2">
          <h2 className="mb-4 text-base font-medium">Create New Video Project</h2>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
            <input placeholder="Project title" value={title} onChange={(e) => setTitle(e.target.value)} className="rounded-lg border border-white/10 bg-[#111522] px-3 py-2 text-sm text-white" />
            <input placeholder="Video topic or idea" value={topic} onChange={(e) => setTopic(e.target.value)} className="rounded-lg border border-white/10 bg-[#111522] px-3 py-2 text-sm text-white" />
            <div className="flex gap-2">
              <select value={format} onChange={(e) => setFormat(e.target.value as any)} className="rounded-lg border border-white/10 bg-[#111522] px-3 py-2 text-sm text-white">
                <option value="long_form">YouTube 16:9</option>
                <option value="shorts">Shorts 9:16</option>
              </select>
              <button onClick={() => createProject.mutate()} disabled={!title || !topic || createProject.isPending} className="flex items-center gap-1.5 rounded-lg bg-[#8B5CF6] px-4 py-2 text-sm font-medium text-white disabled:opacity-50">
                <Plus className="h-4 w-4" /> Create
              </button>
            </div>
          </div>
          <h3 className="mb-3 mt-6 text-sm font-medium text-[#94A3B8]">Recent Projects</h3>
          <div className="space-y-2">
            {(projects.data || []).map((p) => (
              <div key={p.id} onClick={() => setActiveProjectId(p.id)} className={`flex cursor-pointer items-center justify-between rounded-lg border p-3 ${activeProjectId === p.id ? "border-[#8B5CF6] bg-[#8B5CF6]/10" : "border-white/10 bg-[#111522]"}`}>
                <div><div className="text-sm font-medium text-white">{p.title}</div><div className="text-xs text-[#94A3B8]">{p.topic} • {p.aspect_ratio}</div></div>
                <StatusBadge status={p.status} />
              </div>
            ))}
            {projects.data?.length === 0 && <p className="text-xs text-[#94A3B8]">No projects yet. Create your first project above.</p>}
          </div>
        </div>
        <div className="space-y-6">
          <div className="rounded-xl border border-white/10 bg-[#171C2B] p-5">
            <h2 className="mb-3 text-base font-medium">AI Provider Status</h2>
            <div className="space-y-2">
              {(providers.data || []).map((pr) => (
                <div key={pr.slug} className="flex items-center justify-between text-xs"><span className="text-[#F8FAFC]">{pr.display_name}</span><StatusBadge status={pr.connection_status} /></div>
              ))}
            </div>
          </div>
          <div className="rounded-xl border border-white/10 bg-[#171C2B] p-5">
            <h2 className="mb-3 text-base font-medium">Rendering Queue</h2>
            <div className="space-y-2">
              {(jobs.data || []).slice(0, 5).map((j) => (
                <div key={j.id} className="rounded-lg bg-[#111522] p-2.5 text-xs">
                  <div className="flex justify-between"><span className="font-medium text-white">{j.job_type}</span><span className="text-[#94A3B8]">{j.status} ({j.progress_percent}%)</span></div>
                  {j.error_message && <p className="mt-1 text-[#EF4444]">{j.error_message}</p>}
                </div>
              ))}
              {jobs.data?.length === 0 && <p className="text-xs text-[#94A3B8]">Queue is idle.</p>}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
