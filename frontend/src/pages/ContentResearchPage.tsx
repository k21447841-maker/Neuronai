import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Search } from "lucide-react";
import { apiFetch } from "../services/api";
import { useAppStore } from "../stores/appStore";

export function ContentResearchPage() {
  const qc = useQueryClient();
  const { activeProjectId, setActiveProjectId } = useAppStore();
  const [topic, setTopic] = useState("");
  const [provider, setProvider] = useState<"gemini" | "deepseek" | "claude">("gemini");
  const [result, setResult] = useState<any>(null);

  const research = useMutation({
    mutationFn: async () => {
      let pid = activeProjectId;
      if (!pid) {
        const proj = await apiFetch<any>("/api/projects", {
          method: "POST",
          body: JSON.stringify({ title: topic.slice(0, 60), topic, format: "long_form", aspect_ratio: "16:9", target_duration_seconds: 240 }),
        });
        pid = proj.id;
        setActiveProjectId(pid);
        qc.invalidateQueries({ queryKey: ["projects"] });
      }
      const gen = await apiFetch<any>("/api/scripts/generate", {
        method: "POST",
        body: JSON.stringify({ project_id: pid, topic: `Research outline & viral angles for: ${topic}`, niche: "Research", provider_slug: provider, duration_seconds: 240, tone: "analytical" }),
      });
      const full = await apiFetch<any>(`/api/scripts/project/${pid}`);
      setResult(full);
      return gen;
    },
  });

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">AI Content Research & Structuring</h1>
      <div className="rounded-xl border border-white/10 bg-[#171C2B] p-5 space-y-4">
        <div className="flex flex-col gap-3 sm:flex-row">
          <input placeholder="Enter topic or niche to research..." value={topic} onChange={(e) => setTopic(e.target.value)} className="flex-1 rounded-lg border border-white/10 bg-[#111522] px-3 py-2 text-sm text-white" />
          <select value={provider} onChange={(e) => setProvider(e.target.value as any)} className="rounded-lg border border-white/10 bg-[#111522] px-3 py-2 text-sm text-white">
            <option value="gemini">Gemini (Research)</option>
            <option value="deepseek">DeepSeek (Reasoning)</option>
            <option value="claude">Claude (Synthesis)</option>
          </select>
          <button onClick={() => research.mutate()} disabled={!topic.trim() || research.isPending} className="flex items-center justify-center gap-2 rounded-lg bg-[#8B5CF6] px-4 py-2 text-sm font-medium text-white disabled:opacity-40">
            <Search className="h-4 w-4" /> {research.isPending ? "Researching..." : "Research & Structure"}
          </button>
        </div>
        {research.error && <p className="text-xs text-[#EF4444] break-words">{(research.error as Error).message}</p>}
        {result?.script && (
          <div className="space-y-3 rounded-lg bg-[#111522] p-4 text-sm">
            <div className="text-xs font-medium text-[#22C55E]">Structured outline & {result.scenes?.length || 0} scenes saved!</div>
            <pre className="whitespace-pre-wrap font-sans text-xs leading-relaxed text-[#F8FAFC]">{result.script.full_text}</pre>
          </div>
        )}
      </div>
    </div>
  );
}
