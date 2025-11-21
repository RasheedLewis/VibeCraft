export const RequirementPill: React.FC<{ icon: React.ReactNode; label: string }> = ({
  icon,
  label,
}) => (
  <div className="inline-flex items-center gap-2 rounded-full border border-vc-border/40 bg-[rgba(255,255,255,0.02)] px-3 py-1.5 text-xs text-vc-text-secondary shadow-vc1">
    <span className="text-vc-accent-primary">{icon}</span>
    <span>{label}</span>
  </div>
)
