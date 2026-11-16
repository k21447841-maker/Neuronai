import { useState } from "react";
import { Outlet } from "react-router-dom";
import { Menu, LogOut } from "lucide-react";
import { Sidebar } from "./Sidebar";
import { supabase } from "../../lib/supabase";
import { getApiBase } from "../../services/api";

export function AppShell() {
  const [mobileOpen, setMobileOpen] = useState(false);
  const hasServer = Boolean(getApiBase());

  return (
    <div className="flex min-h-screen bg-[#090B12] text-[#F8FAFC]">
      <Sidebar mobileOpen={mobileOpen} onCloseMobile={() => setMobileOpen(false)} />
      <div className="flex flex-1 flex-col min-w-0">
        <header className="flex h-16 items-center justify-between border-b border-white/10 bg-[#111522]/80 px-4 lg:px-8">
          <button onClick={() => setMobileOpen(true)} className="rounded-lg p-2 text-[#94A3B8] hover:bg-white/5 lg:hidden" aria-label="Open menu">
            <Menu className="h-5 w-5" />
          </button>
          <div className="text-xs font-medium uppercase tracking-wider text-[#94A3B8]">
            {hasServer ? "AI YouTube Studio • Cloud" : "NEUROFLOW AI • Standalone App"}
          </div>
          {hasServer ? (
            <button onClick={() => supabase.auth.signOut()} className="flex items-center gap-2 rounded-lg border border-white/10 px-3 py-1.5 text-xs font-medium text-[#94A3B8] hover:bg-white/5 hover:text-white">
              <LogOut className="h-3.5 w-3.5" /> Sign Out
            </button>
          ) : (
            <span className="rounded-full bg-[#22C55E]/15 px-2.5 py-1 text-[11px] font-medium text-[#22C55E]">On-Device Ready</span>
          )}
        </header>
        <main className="flex-1 p-4 lg:p-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
