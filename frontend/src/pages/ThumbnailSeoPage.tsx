import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { Download, Image as ImageIcon } from "lucide-react";
import { apiFetch } from "../services/api";
import { useAppStore } from "../stores/appStore";

export function ThumbnailSeoPage() {
  const { activeProjectId } = useAppStore();
  const [thumbPrompt, setThumbPrompt] = useState("");
  const [overlayText, setOverlayText] = useState("HOW AI WORKS");
  const [textColor, setTextColor] = useState("#FFFFFF");
  const [bgAccent, setBgAccent] = useState("#8B5CF6");

  const genThumb = useMutation({
    mutationFn: () => apiFetch<any>("/api/media/visuals/generate", { method: "POST", body: JSON.stringify({ project_id: activeProjectId || "default", provider_slug: "openai_images", prompt: thumbPrompt, width: 1280, height: 720, asset_kind: "thumbnail" }) }),
  });

  function downloadPng() {
    const canvas = document.createElement("canvas");
    canvas.width = 1280;
    canvas.height = 720;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const drawTextAndSave = () => {
      ctx.fillStyle = "rgba(0,0,0,0.35)";
      ctx.fillRect(0, 520, 1280, 200);
      ctx.font = "900 84px sans-serif";
      ctx.fillStyle = textColor;
      ctx.shadowColor = "rgba(0,0,0,0.9)";
      ctx.shadowBlur = 16;
      ctx.fillText(overlayText, 48, 640);
      const a = document.createElement("a");
      a.href = canvas.toDataURL("image/png");
      a.download = "neuroflow_thumbnail.png";
      a.click();
    };

    if (genThumb.data?.url) {
      const img = new Image();
      img.crossOrigin = "anonymous";
      img.onload = () => { ctx.drawImage(img, 0, 0, 1280, 720); drawTextAndSave(); };
      img.src = genThumb.data.url;
    } else {
      const grad = ctx.createLinearGradient(0, 0, 1280, 720);
      grad.addColorStop(0, "#090B12");
      grad.addColorStop(1, bgAccent);
      ctx.fillStyle = grad;
      ctx.fillRect(0, 0, 1280, 720);
      drawTextAndSave();
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Thumbnail Studio (16:9 PNG Export)</h1>
      <div className="rounded-xl border border-white/10 bg-[#171C2B] p-5 space-y-4">
        <input placeholder="Optional AI background prompt (requires OpenAI key)..." value={thumbPrompt} onChange={(e) => setThumbPrompt(e.target.value)} className="w-full rounded-lg border border-white/10 bg-[#111522] px-3 py-2 text-sm text-white" />
        <div className="flex flex-wrap items-center gap-2">
          <input placeholder="Overlay Headline" value={overlayText} onChange={(e) => setOverlayText(e.target.value)} className="min-w-[160px] flex-1 rounded-lg border border-white/10 bg-[#111522] px-3 py-2 text-sm text-white" />
          <input type="color" title="Text color" value={textColor} onChange={(e) => setTextColor(e.target.value)} className="h-10 w-10 rounded bg-transparent" />
          <input type="color" title="Gradient accent" value={bgAccent} onChange={(e) => setBgAccent(e.target.value)} className="h-10 w-10 rounded bg-transparent" />
          <button onClick={() => genThumb.mutate()} disabled={!thumbPrompt.trim() || genThumb.isPending} className="flex items-center gap-1.5 rounded-lg bg-[#8B5CF6] px-4 py-2 text-xs font-medium text-white disabled:opacity-40">
            <ImageIcon className="h-4 w-4" /> AI BG
          </button>
          <button onClick={downloadPng} className="flex items-center gap-1.5 rounded-lg bg-[#22C55E] px-4 py-2 text-xs font-medium text-black">
            <Download className="h-4 w-4" /> Download 16:9 PNG
          </button>
        </div>
        <div style={{ background: `linear-gradient(135deg, #090B12, ${bgAccent})` }} className="relative flex aspect-video items-center justify-center overflow-hidden rounded-lg border border-white/10">
          {genThumb.data?.url && <img src={genThumb.data.url} alt="Thumbnail" className="h-full w-full object-cover" />}
          <span style={{ color: textColor }} className="absolute bottom-4 left-4 text-2xl font-black drop-shadow-[0_2px_6px_rgba(0,0,0,0.9)]">{overlayText}</span>
        </div>
        {genThumb.error && <p className="text-xs text-[#EF4444] break-words">{(genThumb.error as Error).message}</p>}
      </div>
    </div>
  );
}
