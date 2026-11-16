import { create } from "zustand";

interface AppState {
  sidebarCollapsed: boolean;
  activeProjectId: string | null;
  toggleSidebar: () => void;
  setActiveProjectId: (id: string | null) => void;
}

export const useAppStore = create<AppState>((set) => ({
  sidebarCollapsed: false,
  activeProjectId: null,
  toggleSidebar: () => set((s) => ({ sidebarCollapsed: !s.sidebarCollapsed })),
  setActiveProjectId: (id) => set({ activeProjectId: id }),
}));
