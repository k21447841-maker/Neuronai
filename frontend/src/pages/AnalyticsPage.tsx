import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "../services/api";

export function AnalyticsPage() {
  const yt = useQuery({ queryKey: ["yt-analytics"], queryFn: () => apiFetch<{ videos: any[] }>("/api/analytics/youtube") });
  return (
    <div className="space-y-6">
      <div><h1 className="text-2xl font-semibold">YouTube Analytics (Official API Metrics)</h1><p className="text-sm text-[#94A3B8]">Live metrics retrieved directly from YouTube Data API v3.</p></div>
      {yt.error && <div className="rounded-lg border border-[#EF4444]/40 bg-[#EF4444]/10 p-3 text-xs text-[#EF4444]">{(yt.error as Error).message}</div>}
      <div className="rounded-xl border border-white/10 bg-[#171C2B] overflow-hidden">
        <table className="w-full text-left text-sm">
          <thead className="border-b border-white/10 bg-[#111522] text-xs uppercase text-[#94A3B8]">
            <tr><th className="px-4 py-3">Video Title</th><th className="px-4 py-3">Published</th><th className="px-4 py-3">Views</th><th className="px-4 py-3">Likes</th><th className="px-4 py-3">Comments</th></tr>
          </thead>
          <tbody className="divide-y divide-white/10">
            {(yt.data?.videos || []).map((v) => (
              <tr key={v.youtube_video_id} className="hover:bg-white/5">
                <td className="px-4 py-3 font-medium text-white">{v.title}</td>
                <td className="px-4 py-3 text-xs text-[#94A3B8]">{new Date(v.published_at).toLocaleDateString()}</td>
                <td className="px-4 py-3 text-[#F8FAFC]">{v.views.toLocaleString()}</td>
                <td className="px-4 py-3 text-[#22C55E]">{v.likes.toLocaleString()}</td>
                <td className="px-4 py-3 text-[#3B82F6]">{v.comments.toLocaleString()}</td>
              </tr>
            ))}
            {(!yt.data?.videos || yt.data.videos.length === 0) && <tr><td colSpan={5} className="px-4 py-8 text-center text-xs text-[#94A3B8]">No published YouTube videos found yet.</td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  );
}
