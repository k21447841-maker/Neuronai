import { useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { Image as ImageIcon, UploadCloud } from "lucide-react";
import { apiFetch } from "../services/api";
import { useAppStore } from "../stores/appStore";

export function ThumbnailSeoPage() {
  const { activeProjectId } = useAppStore();
  const [thumbPrompt, setThumbPrompt] = useState("");
  const [overlayText, setOverlayText] = useState("HOW AI WORKS");
  const [textColor, setTextColor] = useState("#FFFFFF");
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [tags, setTags] = useState("");
  const [channelId, setChannelId] = useState("");
  const [videoId, setVideoId] = useState("");
  const [privacy, setPrivacy] = useState<"private" | "unlisted" | "public">("private");
  const [scheduledAt, setScheduledAt] = useState("");

  const channels = useQuery({ queryKey: ["yt-channels"], queryFn: () => apiFetch<any[]>("/api/youtube/channels") });
  const library = useQuery({ queryKey: ["library"], queryFn: () => apiFetch<any>("/api/library") });
  const genThumb = useMutation({ mutationFn: () => apiFetch<any>("/api/media/visuals/generate", { method: "POST", body: JSON.stringify({ project_id: activeProjectId || "default", provider_slug: "openai_images", prompt: thumbPrompt, width: 1280, height: 720, asset_kind: "thumbnail" }) }) });
  const publishVideo = useMutation({
    mutationFn: () => apiFetch<any>("/api/youtube/upload", { method: "POST", body: JSON.stringify({ project_id: activeProjectId, channel_id: channelId, video_id: videoId, thumbnail_image_id: genThumb.data?.image_id, title, description, tags: tags.split(",").map((t) => t.trim()).filter(Boolean), privacy_status: privacy, scheduled_publish_at: scheduledAt ? new Date(scheduledAt).toISOString() : null }) }),
  });

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Thumbnail Studio, SEO & Publishing</h1>
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="rounded-xl border border-white/10 bg-[#171C2B] p-5 space-y-4">
          <h2 className="text-base font-medium">16:9 Thumbnail Canvas & Generator</h2>
          <input placeholder="Thumbnail visual prompt..." value={thumbPrompt} onChange={(e) => setThumbPrompt(e.target.value)} className="w-full rounded-lg border border-white/10 bg-[#111522] px-3 py-2 text-sm" />
          <div className="flex gap-3">
            <input placeholder="Overlay Headline" value={overlayText} onChange={(e) => setOverlayText(e.target.value)} className="flex-1 rounded-lg border border-white/10 bg-[#111522] px-3 py-2 text-sm" />
            <input type="color" value={textColor} onChange={(e) => setTextColor(e.target.value)} className="h-10 w-12 rounded bg-transparent" />
            <button onClick={() => genThumb.mutate()} disabled={!thumbPrompt || genThumb.isPending} className="flex items-center gap-1.5 rounded-lg bg-[#8B5CF6] px-4 py-2 text-xs font-medium text-white disabled:opacity-40"><ImageIcon className="h-4 w-4" /> Generate</button>
          </div>
          <div className="relative flex aspect-video items-center justify-center overflow-hidden rounded-lg border border-white/10 bg-[#090B12]">
            {genThumb.data?.url && <img src={genThumb.data.url} alt="Thumbnail" className="h-full w-full object-cover" />}
            <span style={{ color: textColor }} className="absolute bottom-4 left-4 text-2xl font-black drop-shadow-[0_2px_6px_rgba(0,0,0,0.9)]">{overlayText}</span>
          </div>
          {genThumb.error && <p className="text-xs text-[#EF4444]">{(genThumb.error as Error).message}</p>}
        </div>
        <div className="rounded-xl border border-white/10 bg-[#171C2B] p-5 space-y-3">
          <h2 className="text-base font-medium">YouTube Metadata & Upload / Schedule</h2>
          <select value={channelId} onChange={(e) => setChannelId(e.target.value)} className="w-full rounded-lg border border-white/10 bg-[#111522] px-3 py-2 text-sm"><option value="">Select connected YouTube channel...</option>{(channels.data || []).map((c) => <option key={c.id} value={c.id}>{c.channel_title}</option>)}</select>
          <select value={videoId} onChange={(e) => setVideoId(e.target.value)} className="w-full rounded-lg border border-white/10 bg-[#111522] px-3 py-2 text-sm"><option value="">Select rendered video...</option>{(library.data?.videos || []).map((v: any) => <option key={v.id} value={v.id}>{v.kind} ({v.resolution}) — {v.id.slice(0, 8)}</option>)}</select>
          <input placeholder="YouTube Video Title" value={title} onChange={(e) => setTitle(e.target.value)} className="w-full rounded-lg border border-white/10 bg-[#111522] px-3 py-2 text-sm" />
          <textarea rows={3} placeholder="Description & #hashtags..." value={description} onChange={(e) => setDescription(e.target.value)} className="w-full rounded-lg border border-white/10 bg-[#111522] p-3 text-sm" />
          <input placeholder="Tags (comma separated)" value={tags} onChange={(e) => setTags(e.target.value)} className="w-full rounded-lg border border-white/10 bg-[#111522] px-3 py-2 text-sm" />
          <div className="grid grid-cols-2 gap-3">
            <select value={privacy} onChange={(e) => setPrivacy(e.target.value as any)} className="rounded-lg border border-white/10 bg-[#111522] px-3 py-2 text-sm"><option value="private">Private</option><option value="unlisted">Unlisted</option><option value="public">Public</option></select>
            <input type="datetime-local" value={scheduledAt} onChange={(e) => setScheduledAt(e.target.value)} className="rounded-lg border border-white/10 bg-[#111522] px-3 py-2 text-sm" />
          </div>
          <button onClick={() => publishVideo.mutate()} disabled={!activeProjectId || !channelId || !videoId || !title || publishVideo.isPending} className="flex w-full items-center justify-center gap-2 rounded-lg bg-[#3B82F6] py-2.5 text-sm font-medium text-white disabled:opacity-40"><UploadCloud className="h-4 w-4" /> {scheduledAt ? "Schedule YouTube Upload" : "Upload to YouTube Now"}</button>
          {publishVideo.data && <p className="text-xs text-[#22C55E]">Upload status: {publishVideo.data.upload_status} (ID: {publishVideo.data.upload_id})</p>}
          {publishVideo.error && <p className="text-xs text-[#EF4444]">{(publishVideo.error as Error).message}</p>}
        </div>
      </div>
    </div>
  );
}
