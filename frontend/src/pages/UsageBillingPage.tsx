import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "../services/api";

export function UsageBillingPage() {
  const logs = useQuery({ queryKey: ["usage-logs"], queryFn: () => apiFetch<any[]>("/api/usage") });
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Usage & Provider Consumption</h1>
      <div className="rounded-xl border border-white/10 bg-[#171C2B] overflow-hidden">
        <table className="w-full text-left text-sm">
          <thead className="border-b border-white/10 bg-[#111522] text-xs uppercase text-[#94A3B8]">
            <tr><th className="px-4 py-3">Provider</th><th className="px-4 py-3">Operation</th><th className="px-4 py-3">Units</th><th className="px-4 py-3">Timestamp</th></tr>
          </thead>
          <tbody className="divide-y divide-white/10">
            {(logs.data || []).map((l) => (
              <tr key={l.id}><td className="px-4 py-3 font-medium text-white">{l.provider_slug}</td><td className="px-4 py-3 text-[#94A3B8]">{l.operation}</td><td className="px-4 py-3">{l.units_consumed} {l.unit_type}</td><td className="px-4 py-3 text-xs text-[#94A3B8]">{new Date(l.created_at).toLocaleString()}</td></tr>
            ))}
            {logs.data?.length === 0 && <tr><td colSpan={4} className="px-4 py-6 text-center text-xs text-[#94A3B8]">No provider usage logged yet.</td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  );
}
