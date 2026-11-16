import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { Layers } from "lucide-react";
import { apiFetch } from "../services/api";
import { useAppStore } from "../stores/appStore";

export function Animation2DPage() {
  const { activeProjectId } = useAppStore();
  const [prompt, setPrompt] = useState("");
  const [preset, setPreset] = useState("Cinematic illustration");
  const [provider, setProvider] = useState("openai_images");
  const gen = useMutation({
    mutationFn: () => apiFetch<any>("/api/media/visuals/generate", { method: "POST", body: JSON.stringify({ project_id: activeProjectId || "default", provider_slug: provider, prompt: `${preset} style: ${prompt}`, width: 1920, height: 1080, asset_kind: "scene_frame" }) }),
  });

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">2D Animation & Visual Asset Studio</h1>
      <div className="rounded-xl border border-white/10 bg-[#171C2B] p-5 space-y-4">
        <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
          <select value={preset} onChange={(e) => setPreset(e.target.value)} className="rounded-lg border border-white/10 bg-[#111522] px-3 py-2 text-sm">
            {["Cartoon", "Anime", "Educational", "Whiteboard animation", "Motion graphics", "Cinematic illustration", "Explainer animation"].map((p) => <option key={p} value={p}>{p}</option>)}
          </select>
          <select value={provider} onChange={(e) => setProvider(e.target.value)} className="rounded-lg border border-white/10 bg-[#111522] px-3 py-2 text-sm">
            <option value="openai_images">OpenAI Visual / DALL-E</option><option value="stability">Stability AI</option>
          </select>
        </div>
        <textarea rows={3} placeholder="Describe scene characters, background, and lighting..." value={prompt} onChange={(e) => setPrompt(e.target.value)} className="w-full rounded-lg border border-white/10 bg-[#111522] p-3 text-sm" />
        <button onClick={() => gen.mutate()} disabled={!prompt || gen.isPending} className="flex items-center gap-2 rounded-lg bg-[#8B5CF6] px-4 py-2 text-sm font-medium text-white disabled:opacity-40"><Layers className="h-4 w-4" /> {gen.isPending ? "Generating Asset..." : "Generate Scene Frame"}</button>
        {gen.error && <p className="text-xs text-[#EF4444]">{(gen.error as Error).message}</p>}
        {gen.data?.url && <img src={gen.data.url} alt="Generated scene" className="max-h-80 rounded-lg border border-white/10" />}
      </div>
    </div>
  );
}
