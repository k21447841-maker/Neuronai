import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Youtube, Trash2, Link2 } from "lucide-react";
import { apiFetch } from "../services/api";

export function YouTubeChannelsPage() {
  const qc = useQueryClient();
  const channels = useQuery({ queryKey: ["yt-channels"], queryFn: () => apiFetch<any[]>("/api/youtube/channels") });
  const connect = useMutation({
    mutationFn: () => apiFetch<{ authorization_url: string }>("/api/youtube/oauth/start"),
    onSuccess: (d) => { window.location.href = d.authorization_url; },
  });
  const disconnect = useMutation({
    mutationFn: (id: string) => apiFetch(`/api/youtube/channels/${id}`, { method: "DELETE" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["yt-channels"] }),
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div><h1 className="text-2xl font-semibold">YouTube Channels (OAuth 2.0)</h1><p className="text-sm text-[#94A3B8]">Connect multiple channels using official Google OAuth consent.</p></div>
        <button onClick={() => connect.mutate()} className="flex items-center gap-2 rounded-lg bg-[#8B5CF6] px-4 py-2 text-sm font-medium text-white"><Link2 className="h-4 w-4" /> Connect YouTube Channel</button>
      </div>
      {connect.error && <p className="text-xs text-[#EF4444]">{(connect.error as Error).message}</p>}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        {(channels.data || []).map((c) => (
          <div key={c.id} className="flex items-center justify-between rounded-xl border border-white/10 bg-[#171C2B] p-4">
            <div className="flex items-center gap-3">
              {c.thumbnail_url ? <img src={c.thumbnail_url} className="h-10 w-10 rounded-full" /> : <Youtube className="h-8 w-8 text-[#EF4444]" />}
              <div><div className="font-medium text-white">{c.channel_title}</div><div className="text-xs text-[#94A3B8]">{c.subscriber_count} subscribers • {c.video_count} videos • {c.status}</div></div>
            </div>
            <button onClick={() => disconnect.mutate(c.id)} className="rounded p-2 text-[#94A3B8] hover:text-[#EF4444]"><Trash2 className="h-4 w-4" /></button>
          </div>
        ))}
        {channels.data?.length === 0 && <p className="text-sm text-[#94A3B8]">No channels connected yet.</p>}
      </div>
    </div>
  );
}
