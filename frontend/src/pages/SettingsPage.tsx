import { ChangeEvent, useState } from "react";
import { Download, Upload } from "lucide-react";

const STORE_KEY = "neuroflow_standalone_db_v1";

export function SettingsPage() {
  const [mode, setMode] = useState(localStorage.getItem("neuroflow_run_mode") || "standalone");
  const [backendUrl, setBackendUrl] = useState(localStorage.getItem("neuroflow_custom_backend_url") || "");
  const [msg, setMsg] = useState<string | null>(null);

  function saveSettings() {
    localStorage.setItem("neuroflow_run_mode", mode);
    if (mode === "cloud" && backendUrl.trim()) {
      localStorage.setItem("neuroflow_custom_backend_url", backendUrl.trim().replace(/\/$/, ""));
    } else {
      localStorage.setItem("neuroflow_run_mode", "standalone");
      setMode("standalone");
    }
    setMsg("Settings saved! Reloading mode...");
    setTimeout(() => window.location.reload(), 600);
  }

  function exportLocalDataFile() {
    const raw = localStorage.getItem(STORE_KEY) || "{}";
    const blob = new Blob([raw], { type: "application/json" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "neuroflow_phone_data.json";
    a.click();
    setMsg("Saved backup file: neuroflow_phone_data.json");
  }

  function importLocalDataFile(e: ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      try {
        JSON.parse(String(reader.result));
        localStorage.setItem(STORE_KEY, String(reader.result));
        setMsg("Local phone data file restored!");
      } catch {
        setMsg("Invalid JSON backup file.");
      }
    };
    reader.readAsText(file);
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">App Settings & Local Data File</h1>
      <div className="max-w-lg rounded-xl border border-white/10 bg-[#171C2B] p-5 space-y-4">
        <div>
          <label className="mb-1 block text-xs text-[#94A3B8]">App Mode</label>
          <select value={mode} onChange={(e) => setMode(e.target.value)} className="w-full rounded-lg border border-white/10 bg-[#111522] px-3 py-2 text-sm text-white">
            <option value="standalone">Standalone On-Device Mode (No Server Needed)</option>
            <option value="cloud">Cloud Backend Mode (Optional)</option>
          </select>
        </div>
        {mode === "cloud" && (
          <div>
            <label className="mb-1 block text-xs text-[#94A3B8]">Cloud Backend URL</label>
            <input placeholder="https://your-backend.onrender.com" value={backendUrl} onChange={(e) => setBackendUrl(e.target.value)} className="w-full rounded-lg border border-white/10 bg-[#111522] px-3 py-2 text-sm text-white" />
          </div>
        )}
        <button onClick={saveSettings} className="rounded-lg bg-[#8B5CF6] px-4 py-2 text-sm font-medium text-white">Save Mode</button>

        <div className="border-t border-white/10 pt-4 space-y-3">
          <h2 className="text-sm font-medium text-white">Phone Local File Backup (neuroflow_phone_data.json)</h2>
          <p className="text-xs text-[#94A3B8]">All scripts, projects, voices, and keys auto-save on phone. Export/Import anytime as one local file:</p>
          <div className="flex flex-wrap gap-3">
            <button onClick={exportLocalDataFile} className="flex items-center gap-1.5 rounded-lg bg-[#22C55E]/20 border border-[#22C55E]/40 px-3 py-2 text-xs font-medium text-[#22C55E]">
              <Download className="h-4 w-4" /> Save File to Phone
            </button>
            <label className="flex cursor-pointer items-center gap-1.5 rounded-lg border border-white/10 bg-[#111522] px-3 py-2 text-xs font-medium text-white">
              <Upload className="h-4 w-4" /> Load Backup File
              <input type="file" accept=".json" onChange={importLocalDataFile} className="hidden" />
            </label>
          </div>
        </div>
        {msg && <p className="text-xs text-[#22C55E]">{msg}</p>}
      </div>
    </div>
  );
}
