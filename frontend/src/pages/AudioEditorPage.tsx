import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Sliders, Download } from "lucide-react";
import { apiFetch } from "../services/api";

export function AudioEditorPage() {
  const qc = useQueryClient();
  const [audioId, setAudioId] = useState("");
  const [thresholdDb, setThresholdDb] = useState(-35);
  const [minSilence, setMinSilence] = useState(0.45);
  const [retainPause, setRetainPause] = useState(0.18);
  const [noiseReduction, setNoiseReduction] = useState(true);
  const library = useQuery({ queryKey: ["library"], queryFn: () => apiFetch<any>("/api/library") });

  const editAudio = useMutation({
    mutationFn: () =>
      apiFetch<any>("/api/voice/audio/edit", {
        method: "POST",
        body: JSON.stringify({
          audio_id: audioId,
          silence_threshold_db: thresholdDb,
          min_silence_duration: minSilence,
          retain_pause_seconds: retainPause,
          noise_reduction: noiseReduction,
          normalize_loudness: true,
        }),
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["library"] }),
  });

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Audio Editor & Silence Trimmer</h1>
      <div className="rounded-xl border border-white/10 bg-[#171C2B] p-5 space-y-4">
        <select value={audioId} onChange={(e) => setAudioId(e.target.value)} className="w-full rounded-lg border border-white/10 bg-[#111522] px-3 py-2 text-sm text-white">
          <option value="">Select generated audio track...</option>
          {(library.data?.audios || []).map((a: any) => (
            <option key={a.id} value={a.id}>{a.voice_name || "Narration"} ({a.duration_seconds}s) — {a.id.slice(0, 8)}</option>
          ))}
        </select>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-3 text-xs text-[#94A3B8]">
          <label>Silence Threshold ({thresholdDb} dB)<input type="range" min="-60" max="-15" value={thresholdDb} onChange={(e) => setThresholdDb(Number(e.target.value))} className="w-full" /></label>
          <label>Min Silence ({minSilence}s)<input type="range" min="0.2" max="2.0" step="0.05" value={minSilence} onChange={(e) => setMinSilence(Number(e.target.value))} className="w-full" /></label>
          <label>Retain Natural Pause ({retainPause}s)<input type="range" min="0.05" max="0.6" step="0.02" value={retainPause} onChange={(e) => setRetainPause(Number(e.target.value))} className="w-full" /></label>
        </div>
        <label className="flex items-center gap-2 text-xs text-[#F8FAFC]"><input type="checkbox" checked={noiseReduction} onChange={(e) => setNoiseReduction(e.target.checked)} /> Trim leading/trailing silence & export clean WAV</label>
        <button onClick={() => editAudio.mutate()} disabled={!audioId || editAudio.isPending} className="flex items-center gap-2 rounded-lg bg-[#8B5CF6] px-4 py-2 text-sm font-medium text-white disabled:opacity-40">
          <Sliders className="h-4 w-4" /> {editAudio.isPending ? "Trimming..." : "Trim Silence & Process"}
        </button>
        {editAudio.error && <p className="text-xs text-[#EF4444]">{(editAudio.error as Error).message}</p>}
        {editAudio.data?.processed_url && (
          <div className="space-y-2 rounded-lg bg-[#111522] p-3">
            <audio controls src={editAudio.data.processed_url} className="w-full" />
            <a href={editAudio.data.processed_url} download="neuroflow_trimmed.wav" className="inline-flex items-center gap-1.5 text-xs text-[#22C55E] underline">
              <Download className="h-3.5 w-3.5" /> Download Trimmed WAV
            </a>
          </div>
        )}
      </div>
    </div>
  );
}
