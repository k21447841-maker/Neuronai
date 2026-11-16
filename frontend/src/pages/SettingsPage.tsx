import { useState } from "react";

export function SettingsPage() {
  const [backendUrl, setBackendUrl] = useState(localStorage.getItem("neuroflow_custom_backend_url") || "");
  const [saved, setSaved] = useState(false);

  function saveSettings() {
    if (backendUrl.trim()) {
      localStorage.setItem("neuroflow_custom_backend_url", backendUrl.trim().replace(/\/$/, ""));
    } else {
      localStorage.removeItem("neuroflow_custom_backend_url");
    }
    setSaved(true);
    setTimeout(() => setSaved(false), 2500);
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">App Settings</h1>
      <div className="max-w-lg rounded-xl border border-white/10 bg-[#171C2B] p-5 space-y-4">
        <div className="rounded-lg bg-[#22C55E]/10 border border-[#22C55E]/30 p-3 text-xs text-[#22C55E]">
          Mode: {backendUrl.trim() ? "Cloud Backend Connected" : "Standalone On-Device Mode (No Server Required)"}
        </div>
        <div>
          <label className="mb-1 block text-xs text-[#94A3B8]">Optional Cloud Backend URL (for Blender 3D / YouTube OAuth)</label>
          <input
            placeholder="Leave empty for Standalone APK mode"
            value={backendUrl}
            onChange={(e) => setBackendUrl(e.target.value)}
            className="w-full rounded-lg border border-white/10 bg-[#111522] px-3 py-2 text-sm text-white"
          />
        </div>
        <button onClick={saveSettings} className="rounded-lg bg-[#8B5CF6] px-4 py-2 text-sm font-medium text-white">
          Save Settings
        </button>
        {saved && <p className="text-xs text-[#22C55E]">Settings saved.</p>}
      </div>
    </div>
  );
}
