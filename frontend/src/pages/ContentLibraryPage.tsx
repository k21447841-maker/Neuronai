import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "../services/api";

export function ContentLibraryPage() {
  const [search, setSearch] = useState("");
  const lib = useQuery({ queryKey: ["library"], queryFn: () => apiFetch<any>("/api/library") });
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-3">
        <h1 className="text-2xl font-semibold">Content Library</h1>
        <input placeholder="Search assets..." value={search} onChange={(e) => setSearch(e.target.value)} className="rounded-lg border border-white/10 bg-[#171C2B] px-3 py-2 text-sm" />
      </div>
      <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
        <div className="rounded-xl border border-white/10 bg-[#171C2B] p-4 space-y-3">
          <h2 className="text-sm font-medium text-[#94A3B8]">Images & Thumbnails ({lib.data?.images?.length || 0})</h2>
          {(lib.data?.images || []).filter((i: any) => i.prompt.toLowerCase().includes(search.toLowerCase())).map((i: any) => (
            <div key={i.id} className="rounded bg-[#111522] p-2.5 text-xs space-y-2">
              {i.url && <img src={i.url} alt={i.prompt} className="w-full rounded object-cover max-h-36" />}
              <div className="truncate">{i.prompt}</div>
              {i.url && <a href={i.url} download={`image_${i.id.slice(0, 6)}.png`} className="text-[#3B82F6] underline block">Download PNG</a>}
            </div>
          ))}
        </div>
        <div className="rounded-xl border border-white/10 bg-[#171C2B] p-4 space-y-3">
          <h2 className="text-sm font-medium text-[#94A3B8]">Voiceovers ({lib.data?.audios?.length || 0})</h2>
          {(lib.data?.audios || []).map((a: any) => (
            <div key={a.id} className="rounded bg-[#111522] p-2.5 text-xs space-y-2">
              <div>{a.voice_name || "ElevenLabs"} • {a.duration_seconds}s</div>
              {a.url && <audio controls src={a.url} className="w-full h-8" />}
              {a.url && <a href={a.url} download={`voice_${a.id.slice(0, 6)}.mp3`} className="text-[#3B82F6] underline block">Download Audio</a>}
            </div>
          ))}
        </div>
        <div className="rounded-xl border border-white/10 bg-[#171C2B] p-4 space-y-3">
          <h2 className="text-sm font-medium text-[#94A3B8]">Rendered Videos ({lib.data?.videos?.length || 0})</h2>
          {(lib.data?.videos || []).map((v: any) => (
            <div key={v.id} className="rounded bg-[#111522] p-2 text-xs">
              <div>{v.kind} • {v.resolution}</div>
              {v.url && <a href={v.url} target="_blank" rel="noreferrer" className="text-[#3B82F6] underline">Preview / Download</a>}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
