export function StatusBadge({ status }: { status: string }) {
  const n = status.toLowerCase();
  const styles =
    ["connected", "completed", "active", "uploaded"].includes(n)
      ? "bg-[#22C55E]/15 text-[#22C55E] border-[#22C55E]/30"
      : ["failed", "error", "stopped"].includes(n)
      ? "bg-[#EF4444]/15 text-[#EF4444] border-[#EF4444]/30"
      : ["running", "queued", "uploading"].includes(n)
      ? "bg-[#3B82F6]/15 text-[#3B82F6] border-[#3B82F6]/30"
      : "bg-white/10 text-[#94A3B8] border-white/10";
  return <span className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium capitalize ${styles}`}>{status}</span>;
}
