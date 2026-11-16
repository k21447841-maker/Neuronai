import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Download, Sparkles } from "lucide-react";
import { apiFetch } from "../services/api";
import { useAppStore } from "../stores/appStore";

const NICHES = ["Educational", "Technology", "Gaming", "Business", "Finance", "History", "Science", "Motivation", "Entertainment", "Documentary", "Facts", "Storytelling", "Mystery", "General Knowledge"];

export function ScriptWriterPage() {
  const qc = useQueryClient();
  const { activeProjectId } = useAppStore();
  const [topic, setTopic] = useState("");
  const [niche, setNiche] = useState("Technology");
  const [provider, setProvider] = useState<"claude" | "deepseek" | "gemini">("claude");
  const [tone, setTone] = useState("Cinematic & Engaging");
  const [language, setLanguage] = useState("en");
  const [duration, setDuration] = useState(180);

  const scriptData = useQuery({ queryKey: ["script", activeProjectId], enabled: Boolean(activeProjectId), queryFn: () => apiFetch<any>(`/api/scripts/project/${activeProjectId}`) });
  const generateMutation = useMutation({
    mutationFn: () => apiFetch("/api/scripts/generate", { method: "POST", body: JSON.stringify({ project_id: activeProjectId, topic, niche, language, duration_seconds: duration, tone, provider_slug: provider }) }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["script", activeProjectId] }),
  });

  function exportTxt() {
    if (!scriptData.data?.script?.full_text) return;
    const a = document.createElement("a");
    a.href = URL.createObjectURL(new Blob([scriptData.data.script.full_text], { type: "text/plain" }));
    a.download = `neuroflow_script_${activeProjectId}.txt`;
    a.click();
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div><h1 className="text-2xl font-semibold">AI Script Writer & Scene Planner</h1><p className="text-sm text-[#94A3B8]">{activeProjectId ? `Active Project: ${activeProjectId}` : "Select or create a project in Overview first."}</p></div>
        <button onClick={exportTxt} disabled={!scriptData.data?.script} className="flex items-center gap-2 rounded-lg border border-white/10 px-3 py-2 text-xs font-medium text-white disabled:opacity-40"><Download className="h-4 w-4" /> Export TXT</button>
      </div>
      <div className="grid grid-cols-1 gap-4 rounded-xl border border-white/10 bg-[#171C2B] p-5 md:grid-cols-3">
        <input placeholder="Video topic..." value={topic} onChange={(e) => setTopic(e.target.value)} className="rounded-lg border border-white/10 bg-[#111522] px-3 py-2 text-sm text-white md:col-span-2" />
        <select value={provider} onChange={(e) => setProvider(e.target.value as any)} className="rounded-lg border border-white/10 bg-[#111522] px-3 py-2 text-sm text-white"><option value="claude">Claude (Storytelling)</option><option value="deepseek">DeepSeek (Structuring)</option><option value="gemini">Gemini (Multimodal)</option></select>
        <select value={niche} onChange={(e) => setNiche(e.target.value)} className="rounded-lg border border-white/10 bg-[#111522] px-3 py-2 text-sm text-white">{NICHES.map((n) => <option key={n} value={n}>{n}</option>)}</select>
        <input value={tone} onChange={(e) => setTone(e.target.value)} placeholder="Tone" className="rounded-lg border border-white/10 bg-[#111522] px-3 py-2 text-sm text-white" />
        <div className="flex gap-2">
          <input type="number" value={duration} onChange={(e) => setDuration(Number(e.target.value))} className="w-24 rounded-lg border border-white/10 bg-[#111522] px-3 py-2 text-sm text-white" />
          <input value={language} onChange={(e) => setLanguage(e.target.value)} placeholder="Lang" className="w-20 rounded-lg border border-white/10 bg-[#111522] px-3 py-2 text-sm text-white" />
          <button onClick={() => generateMutation.mutate()} disabled={!activeProjectId || !topic || generateMutation.isPending} className="flex flex-1 items-center justify-center gap-1.5 rounded-lg bg-[#8B5CF6] px-4 py-2 text-sm font-medium text-white disabled:opacity-50"><Sparkles className="h-4 w-4" /> {generateMutation.isPending ? "Generating..." : "Generate"}</button>
        </div>
      </div>
      {generateMutation.error && <div className="rounded-lg border border-[#EF4444]/40 bg-[#EF4444]/10 p-3 text-xs text-[#EF4444]">{(generateMutation.error as Error).message}</div>}
      {scriptData.data?.script && (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <div className="rounded-xl border border-white/10 bg-[#171C2B] p-5 space-y-3"><h2 className="text-base font-medium">Generated Script (v{scriptData.data.script.current_version})</h2><pre className="whitespace-pre-wrap font-sans text-sm leading-relaxed text-[#F8FAFC]">{scriptData.data.script.full_text}</pre></div>
          <div className="rounded-xl border border-white/10 bg-[#171C2B] p-5 space-y-3">
            <h2 className="text-base font-medium">Scene Breakdown ({scriptData.data.scenes.length} Scenes)</h2>
            <div className="space-y-3 max-h-[540px] overflow-y-auto pr-1">
              {scriptData.data.scenes.map((sc: any) => (
                <div key={sc.id} className="rounded-lg border border-white/10 bg-[#111522] p-3 text-xs space-y-1">
                  <div className="flex justify-between font-medium text-[#8B5CF6]"><span>Scene {sc.scene_number}</span><span>{sc.estimated_duration_seconds}s • {sc.camera_movement}</span></div>
                  <p className="text-[#F8FAFC]">{sc.narration}</p>
                  <p className="text-[#94A3B8]">Visual: {sc.visual_description}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
