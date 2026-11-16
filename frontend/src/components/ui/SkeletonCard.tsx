export function SkeletonCard({ rows = 3 }: { rows?: number }) {
  return (
    <div className="animate-pulse rounded-xl border border-white/10 bg-[#171C2B] p-5 space-y-3">
      <div className="h-4 w-1/3 rounded bg-white/10" />
      {Array.from({ length: rows }).map((_, i) => <div key={i} className="h-3 w-full rounded bg-white/5" />)}
    </div>
  );
}
