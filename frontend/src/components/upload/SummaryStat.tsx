export const SummaryStat: React.FC<{ label: string; value: React.ReactNode }> = ({
  label,
  value,
}) => (
  <div className="rounded-lg border border-vc-border/40 bg-[rgba(12,12,18,0.5)] p-3">
    <p className="text-[11px] uppercase tracking-[0.16em] text-vc-text-muted">{label}</p>
    <p className="mt-2 text-sm text-white">{value}</p>
  </div>
)
