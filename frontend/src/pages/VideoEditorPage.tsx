import { useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { Film, Trash2 } from "lucide-react";
import { apiFetch } from "../services/api";
import { useAppStore } from "../stores/appStore";

export function VideoEditorPage() {
  const { activeProjectId } = useAppStore();
  const [aspectRatio, setAspectRatio] = useState<"16:9" | "9:16" | "1:1">("16:9");
  const [resolution, setResolution] = useState<"720p" | "1080p" | "4k">("1080p");
  const [burnSubtitles, setBurnSubtitles] = useState(true);
  const [zoom, setZoom] = useState(1);
  const scriptInfo = useQuery({ queryKey: ["script", activeProjectId], enabled: Boolean(activeProjectId), queryFn: () => apiFetch<any>(`/api/scripts/project/${activeProjectId}`) });
  const [clips, setClips] = useState<any[]>([]);
  const timelineClips = clips.length ? clips : (scriptInfo.data?.scenes || []).map((s: any) => ({ id: s.id, label: `Scene ${s.scene_number}`, duration: s.estimated_duration_seconds }));

  const renderVideo = useMutation({
    mutationFn: () => apiFetch<any>("/api/media/video/render", { method: "POST", body: JSON.stringify({ project_id: activeProjectId, aspect_ratio: aspectRatio, resolution, burn_subtitles: burnSubtitles, timeline_clips: timelineClips }) }),
  });

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <h1 className="text-2xl font-semibold">Video Editor & Timeline Studio</h1>
        <div className="flex items-center gap-2">
          <select value={aspectRatio} onChange={(e) => setAspectRatio(e.target.value as any)} className="rounded-lg border border-white/10 bg-[#171C2B] px-3 py-1.5 text-xs"><option value="16:9">16:9 Standard</option><option value="9:16">9:16 Shorts</option><option value="1:1">1:1 Square</option></select>
          <select value={resolution} onChange={(e) => setResolution(e.target.value as any)} className="rounded-lg border border-white/10 bg-[#171C2B] px-3 py-1.5 text-xs"><option value="720p">720p</option><option value="1080p">1080p</option><option value="4k">4K</option></select>
          <button onClick={() => renderVideo.mutate()} disabled={!activeProjectId || renderVideo.isPending} className="flex items-center gap-1.5 rounded-lg bg-[#8B5CF6] px-4 py-2 text-xs font-medium text-white disabled:opacity-40"><Film className="h-4 w-4" /> Render Final MP4</button>
        </div>
      </div>
      <div className="rounded-xl border border-white/10 bg-[#171C2B] p-5 space-y-4">
        <div className="flex items-center justify-between text-xs text-[#94A3B8]">
          <span>Multi-Track Timeline (Video • Audio • Subtitles)</span>
          <div className="flex items-center gap-3">
            <label className="flex items-center gap-1.5"><input type="checkbox" checked={burnSubtitles} onChange={(e) => setBurnSubtitles(e.target.checked)} /> Burn Subtitles</label>
            <label className="flex items-center gap-1.5">Zoom <input type="range" min="0.5" max="2.5" step="0.25" value={zoom} onChange={(e) => setZoom(Number(e.target.value))} /></label>
          </div>
        </div>
        <div className="space-y-2 overflow-x-auto rounded-lg bg-[#090B12] p-3">
          <div className="text-[11px] uppercase text-[#94A3B8]">Video / Scene Track</div>
          <div className="flex gap-2">
            {timelineClips.map((c: any, idx: number) => (
              <div key={c.id} style={{ minWidth: `${Math.max(90, c.duration * 22 * zoom)}px` }} className="flex items-center justify-between rounded border border-[#8B5CF6]/40 bg-[#8B5CF6]/20 px-2.5 py-2 text-xs">
                <span>{c.label} ({c.duration}s)</span>
                <button onClick={() => setClips(timelineClips.filter((_: any, i: number) => i !== idx))} title="Delete clip"><Trash2 className="h-3.5 w-3.5 text-[#EF4444]" /></button>
              </div>
            ))}
            {timelineClips.length === 0 && <span className="text-xs text-[#94A3B8]">No scenes loaded.</span>}
          </div>
          <div className="pt-2 text-[11px] uppercase text-[#94A3B8]">Voiceover Audio Track</div>
          <div className="h-8 rounded border border-[#3B82F6]/40 bg-[#3B82F6]/15 px-3 flex items-center text-xs text-[#3B82F6]">Synchronized Narration Waveform Track</div>
          <div className="pt-2 text-[11px] uppercase text-[#94A3B8]">Subtitles Track</div>
          <div className="h-7 rounded border border-[#22C55E]/40 bg-[#22C55E]/15 px-3 flex items-center text-xs text-[#22C55E]">Whisper Word-Timestamped Captions</div>
        </div>
        {renderVideo.data && <p className="text-xs text-[#22C55E]">Render job queued: {renderVideo.data.job_id}</p>}
        {renderVideo.error && <p className="text-xs text-[#EF4444]">{(renderVideo.error as Error).message}</p>}
      </div>
    </div>
  );
}
