#!/usr/bin/env bash
FILE="src/components/layout/AppShell.tsx"
cat << 'TSX' > "$FILE"
import { Outlet } from "react-router-dom";
import { Sidebar } from "./Sidebar";

export function AppShell() {
  return (
    <div className="flex h-screen bg-[#0a0a0f] text-white overflow-hidden">
      <Sidebar />
      <main className="flex-1 overflow-y-auto">
        <Outlet />
      </main>
    </div>
  );
}
TSX
echo "AppShell fixed!"
