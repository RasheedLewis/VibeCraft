import React from 'react'
import clsx from 'clsx'

interface TemplatePillProps {
  label: string
  description?: string
  selected?: boolean
  onClick?: () => void
  className?: string
}

export const TemplatePill: React.FC<TemplatePillProps> = ({
  label,
  description,
  selected,
  onClick,
  className,
}) => (
  <button
    onClick={onClick}
    className={clsx(
      selected ? 'vc-template-pill-selected' : 'vc-template-pill',
      className,
    )}
  >
    <span className="text-xs font-medium uppercase tracking-[0.12em] text-vc-text-secondary">
      Template
    </span>
    <span className="text-sm font-medium text-vc-text-primary">{label}</span>
    {description && (
      <span className="mt-0.5 text-[11px] text-vc-text-secondary">{description}</span>
    )}
  </button>
)
