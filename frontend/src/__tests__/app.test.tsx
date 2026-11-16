import { describe, expect, it } from "vitest";
import { NAV_ITEMS } from "../components/layout/Sidebar";
import { useAppStore } from "../stores/appStore";

describe("NEUROFLOW AI Frontend Core", () => {
  it("exposes all 16 required dashboard navigation routes", () => {
    expect(NAV_ITEMS.length).toBe(16);
  });

  it("toggles sidebar and tracks active project", () => {
    const initial = useAppStore.getState().sidebarCollapsed;
    useAppStore.getState().toggleSidebar();
    expect(useAppStore.getState().sidebarCollapsed).toBe(!initial);
    useAppStore.getState().setActiveProjectId("proj-123");
    expect(useAppStore.getState().activeProjectId).toBe("proj-123");
  });
});
