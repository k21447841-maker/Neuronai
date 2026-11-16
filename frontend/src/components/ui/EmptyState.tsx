import { ReactNode } from "react";

export function EmptyState({ icon, title, description, action }: { icon: ReactNode; title: string; description: string; action?: ReactNode }) {
  return (
    <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-white/15 bg-[#111522]/60 p-8 text-center">
      <div className="mb-3 flex h-11 w-11 items-center justify-center rounded-full bg-[#8B5CF6]/15 text-[#8B5CF6]">{icon}</div>
      <h3 className="text-sm font-semibold text-[#F8FAFC]">{title}</h3>
      <p className="mt-1 max-w-sm text-xs text-[#94A3B8]">{description}</p>
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}
