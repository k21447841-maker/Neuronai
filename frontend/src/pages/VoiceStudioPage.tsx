import { useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { Mic, Volume2 } from "lucide-react";
import { apiFetch } from "../services/api";
import { useAppStore } from "../stores/appStore";

export function VoiceStudioPage() {
  const { activeProjectId } = useAppStore();
  const [text, setText] = useState("");
  const [voiceId, setVoiceId] = useState("");
  const [stability, setStability] = useState(0.5);
  const [speed, setSpeed] = useState(1.0);

  const voices = useQuery({ queryKey: ["elevenlabs-voices"], queryFn: () => apiFetch<{ voices: any[] }>("/api/voice/library"), retry: false });
  const synth = useMutation({
    mutationFn: () => apiFetch<any>("/api/voice/generate", { method: "POST", body: JSON.stringify({ project_id: activeProjectId || "default", text, voice_id: voiceId || voices.data?.voices[0]?.voice_id, stability, similarity_boost: 0.75, speed }) }),
  });

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">ElevenLabs Voice Studio</h1>
      {voices.error && <div className="rounded-lg border border-[#EF4444]/40 bg-[#EF4444]/10 p-3 text-xs text-[#EF4444]">{(voices.error as Error).message}</div>}
      <div className="rounded-xl border border-white/10 bg-[#171C2B] p-5 space-y-4">
        <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
          <select value={voiceId} onChange={(e) => setVoiceId(e.target.value)} className="rounded-lg border border-white/10 bg-[#111522] px-3 py-2 text-sm text-white md:col-span-2">
            {(voices.data?.voices || []).map((v) => <option key={v.voice_id} value={v.voice_id}>{v.name} ({v.category})</option>)}
          </select>
          <label className="text-xs text-[#94A3B8]">Stability ({stability})<input type="range" min="0" max="1" step="0.05" value={stability} onChange={(e) => setStability(Number(e.target.value))} className="w-full" /></label>
          <label className="text-xs text-[#94A3B8]">Speed ({speed}x)<input type="range" min="0.7" max="1.2" step="0.05" value={speed} onChange={(e) => setSpeed(Number(e.target.value))} className="w-full" /></label>
        </div>
        <textarea rows={5} placeholder="Paste scene narration or full script..." value={text} onChange={(e) => setText(e.target.value)} className="w-full rounded-lg border border-white/10 bg-[#111522] p-3 text-sm text-white" />
        <button onClick={() => synth.mutate()} disabled={!text || synth.isPending} className="flex items-center gap-2 rounded-lg bg-[#8B5CF6] px-4 py-2 text-sm font-medium text-white disabled:opacity-50"><Mic className="h-4 w-4" /> {synth.isPending ? "Synthesizing..." : "Generate Voiceover"}</button>
        {synth.data?.audio_url && <div className="rounded-lg bg-[#111522] p-3"><div className="mb-2 flex items-center gap-2 text-xs text-[#22C55E]"><Volume2 className="h-4 w-4" /> Audio ID: {synth.data.audio_id}</div><audio controls src={synth.data.audio_url} className="w-full" /></div>}
      </div>
    </div>
  );
}
