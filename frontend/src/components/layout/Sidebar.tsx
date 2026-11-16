import { NavLink } from "react-router-dom";
import {
  LayoutDashboard, FileText, Search, Layers, Box, Mic, Sliders, Film,
  Image, Youtube, Workflow, FolderOpen, BarChart3, Plug, CreditCard,
  Settings, ChevronLeft, ChevronRight, Sparkles
} from "lucide-react";
import { useAppStore } from "../../stores/appStore";

export const NAV_ITEMS = [
  { to: "/", label: "Overview", icon: LayoutDashboard },
  { to: "/script-writer", label: "AI Script Writer", icon: FileText },
  { to: "/content-research", label: "Content Research", icon: Search },
  { to: "/2d-studio", label: "2D Animation Studio", icon: Layers },
  { to: "/3d-studio", label: "3D Animation Studio", icon: Box },
  { to: "/voice-studio", label: "Voice Studio", icon: Mic },
  { to: "/audio-editor", label: "Audio Editor", icon: Sliders },
  { to: "/video-editor", label: "Video Editor", icon: Film },
  { to: "/thumbnail-studio", label: "Thumbnail Studio", icon: Image },
  { to: "/youtube-channels", label: "YouTube Channels", icon: Youtube },
  { to: "/automation", label: "Automation Center", icon: Workflow },
  { to: "/library", label: "Content Library", icon: FolderOpen },
  { to: "/analytics", label: "Analytics", icon: BarChart3 },
  { to: "/integrations", label: "API Integrations", icon: Plug },
  { to: "/billing", label: "Usage & Billing", icon: CreditCard },
  { to: "/settings", label: "Settings", icon: Settings },
];

export function Sidebar({ mobileOpen, onCloseMobile }: { mobileOpen: boolean; onCloseMobile: () => void }) {
  const { sidebarCollapsed, toggleSidebar } = useAppStore();
  return (
    <aside className={`fixed inset-y-0 left-0 z-40 flex flex-col border-r border-white/10 bg-[#111522] transition-all duration-200 lg:static ${sidebarCollapsed ? "lg:w-20" : "lg:w-64"} ${mobileOpen ? "translate-x-0 w-64" : "-translate-x-full lg:translate-x-0"}`}>
      <div className="flex h-16 items-center justify-between border-b border-white/10 px-4">
        <div className="flex items-center gap-2.5 overflow-hidden">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-[#8B5CF6] to-[#3B82F6]">
            <Sparkles className="h-4 w-4 text-white" />
          </div>
          {!sidebarCollapsed && <span className="text-sm font-semibold tracking-wide text-[#F8FAFC]">NEUROFLOW AI</span>}
        </div>
        <button onClick={toggleSidebar} className="hidden rounded-md p-1.5 text-[#94A3B8] hover:bg-white/5 hover:text-white lg:block" aria-label="Toggle sidebar">
          {sidebarCollapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
        </button>
      </div>
      <nav className="flex-1 space-y-1 overflow-y-auto p-3">
        {NAV_ITEMS.map(({ to, label, icon: Icon }) => (
          <NavLink key={to} to={to} end={to === "/"} onClick={onCloseMobile} className={({ isActive }) => `flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${isActive ? "bg-[#8B5CF6]/15 text-[#F8FAFC] border border-[#8B5CF6]/30" : "text-[#94A3B8] hover:bg-white/5 hover:text-[#F8FAFC]"}`}>
            <Icon className="h-4 w-4 shrink-0 text-[#8B5CF6]" />
            {!sidebarCollapsed && <span className="truncate">{label}</span>}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
