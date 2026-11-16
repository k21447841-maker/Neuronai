import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { Box } from "lucide-react";
import { apiFetch } from "../services/api";
import { useAppStore } from "../stores/appStore";
import { ThreeViewport } from "../components/3d/ThreeViewport";

export function Animation3DPage() {
  const { activeProjectId } = useAppStore();
  const [preset, setPreset] = useState("studio_showcase");
  const [titleText, setTitleText] = useState("NEUROFLOW");
  const [cameraMotion, setCameraMotion] = useState("orbit");
  const [samples, setSamples] = useState(32);

  const render3d = useMutation({
    mutationFn: () => apiFetch<any>("/api/media/3d/render", { method: "POST", body: JSON.stringify({ project_id: activeProjectId || "default", scene_preset: preset, title_text: titleText, camera_motion: cameraMotion, samples, preview_only: samples <= 32 }) }),
  });

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">3D Animation Studio (Three.js + Blender Worker)</h1>
      <div className="rounded-xl border border-white/10 bg-[#171C2B] p-5 space-y-4">
        <ThreeViewport preset={preset} cameraMotion={cameraMotion} />
        <div className="grid grid-cols-1 gap-3 md:grid-cols-4">
          <select value={preset} onChange={(e) => setPreset(e.target.value)} className="rounded-lg border border-white/10 bg-[#111522] px-3 py-2 text-sm"><option value="studio_showcase">Studio Showcase</option><option value="orbit_logo">3D Logo Text</option><option value="abstract_tech">Abstract Tech</option></select>
          <input value={titleText} onChange={(e) => setTitleText(e.target.value)} placeholder="3D Text" className="rounded-lg border border-white/10 bg-[#111522] px-3 py-2 text-sm" />
          <select value={cameraMotion} onChange={(e) => setCameraMotion(e.target.value)} className="rounded-lg border border-white/10 bg-[#111522] px-3 py-2 text-sm"><option value="orbit">Orbit</option><option value="dolly_in">Dolly In</option><option value="pan">Pan</option></select>
          <input type="number" min={8} max={256} value={samples} onChange={(e) => setSamples(Number(e.target.value))} className="rounded-lg border border-white/10 bg-[#111522] px-3 py-2 text-sm" />
        </div>
        <button onClick={() => render3d.mutate()} disabled={render3d.isPending} className="flex items-center gap-2 rounded-lg bg-[#8B5CF6] px-4 py-2 text-sm font-medium text-white disabled:opacity-40"><Box className="h-4 w-4" /> Queue Blender 3D Render</button>
        {render3d.error && <p className="text-xs text-[#EF4444]">{(render3d.error as Error).message}</p>}
        {render3d.data && <p className="text-xs text-[#22C55E]">Blender job queued: {render3d.data.job_id}</p>}
      </div>
    </div>
  );
}
