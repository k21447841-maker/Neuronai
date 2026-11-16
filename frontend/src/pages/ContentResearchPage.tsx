import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { Search } from "lucide-react";
import { apiFetch } from "../services/api";
import { useAppStore } from "../stores/appStore";

export function ContentResearchPage() {
  const { activeProjectId } = useAppStore();
  const [topic, setTopic] = useState("");
  const [provider, setProvider] = useState<"deepseek" | "gemini" | "claude">("deepseek");
  const research = useMutation({
    mutationFn: () => apiFetch<any>("/api/scripts/generate", { method: "POST", body: JSON.stringify({ project_id: activeProjectId, topic: `Research outline & viral angles for: ${topic}`, niche: "Research", provider_slug: provider, duration_seconds: 240, tone: "analytical" }) }),
  });

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">AI Content Research & Structuring</h1>
      <div className="rounded-xl border border-white/10 bg-[#171C2B] p-5 space-y-4">
        <div className="flex flex-col gap-3 sm:flex-row">
          <input placeholder="Enter topic or niche to research..." value={topic} onChange={(e) => setTopic(e.target.value)} className="flex-1 rounded-lg border border-white/10 bg-[#111522] px-3 py-2 text-sm" />
          <select value={provider} onChange={(e) => setProvider(e.target.value as any)} className="rounded-lg border border-white/10 bg-[#111522] px-3 py-2 text-sm"><option value="deepseek">DeepSeek (Reasoning)</option><option value="gemini">Gemini (Research)</option><option value="claude">Claude (Synthesis)</option></select>
          <button onClick={() => research.mutate()} disabled={!activeProjectId || !topic || research.isPending} className="flex items-center gap-2 rounded-lg bg-[#8B5CF6] px-4 py-2 text-sm font-medium text-white disabled:opacity-40"><Search className="h-4 w-4" /> Research & Structure</button>
        </div>
        {research.data && <p className="text-xs text-[#22C55E]">Structured outline and {research.data.scene_count} scenes saved to active project.</p>}
        {research.error && <p className="text-xs text-[#EF4444]">{(research.error as Error).message}</p>}
      </div>
    </div>
  );
}
