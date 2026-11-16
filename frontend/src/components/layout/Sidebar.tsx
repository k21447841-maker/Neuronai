import { NavLink } from "react-router-dom";
import { useAppStore } from "../../stores/appStore";
import { 
  LayoutDashboard, PenTool, Search, Box, Boxes, Mic, Music, Video, 
  Image as ImageIcon, Youtube, Settings, BarChart2, Database, 
  Plug, CreditCard, ChevronLeft, Menu 
} from "lucide-react";

export const NAV_ITEMS = [
  { path: "/", label: "Overview", icon: LayoutDashboard },
  { path: "/script-writer", label: "Script Writer", icon: PenTool },
  { path: "/content-research", label: "Content Research", icon: Search },
  { path: "/2d-studio", label: "2D Animation", icon: Box },
  { path: "/3d-studio", label: "3D Animation", icon: Boxes },
  { path: "/voice-studio", label: "Voice Studio", icon: Mic },
  { path: "/audio-editor", label: "Audio Editor", icon: Music },
  { path: "/video-editor", label: "Video Editor", icon: Video },
  { path: "/thumbnail-studio", label: "Thumbnail & SEO", icon: ImageIcon },
  { path: "/youtube-channels", label: "YouTube Channels", icon: Youtube },
  { path: "/automation", label: "Automation", icon: Settings }, 
  { path: "/library", label: "Content Library", icon: Database },
  { path: "/analytics", label: "Analytics", icon: BarChart2 },
  { path: "/integrations", label: "API Integrations", icon: Plug },
  { path: "/billing", label: "Billing", icon: CreditCard },
  { path: "/settings", label: "Settings", icon: Settings },
];

export function Sidebar() {
  const { sidebarCollapsed, toggleSidebar } = useAppStore();

  return (
    <aside
      className={`${
        sidebarCollapsed ? "w-20" : "w-64"
      } bg-[#0a0a0f]/80 backdrop-blur-xl border-r border-white/10 h-screen flex flex-col transition-all duration-300 ease-in-out`}
    >
      <div className="h-16 flex items-center justify-between px-4 border-b border-white/10">
        {!sidebarCollapsed && (
          <span className="text-xl font-bold bg-gradient-to-r from-purple-400 to-pink-500 bg-clip-text text-transparent">
            NEUROFLOW
          </span>
        )}
        <button
          onClick={toggleSidebar}
          className="p-2 rounded-lg hover:bg-white/10 text-gray-400 hover:text-white transition-colors"
        >
          {sidebarCollapsed ? <Menu size={20} /> : <ChevronLeft size={20} />}
        </button>
      </div>

      <nav className="flex-1 overflow-y-auto py-4 px-2 space-y-1">
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-3 rounded-xl transition-all duration-200 group ${
                isActive
                  ? "bg-purple-600/20 text-purple-400 border border-purple-500/30"
                  : "text-gray-400 hover:bg-white/5 hover:text-white"
              }`
            }
          >
            <item.icon size={20} className="shrink-0" />
            {!sidebarCollapsed && <span className="font-medium text-sm">{item.label}</span>}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
