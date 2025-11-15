import React from 'react'
import clsx from 'clsx'

type VCBadgeTone = 'default' | 'success' | 'warning' | 'danger'

interface VCBadgeProps {
  children: React.ReactNode
  tone?: VCBadgeTone
  className?: string
}

const toneClasses: Record<VCBadgeTone, string> = {
  default: '',
  success: 'vc-badge-success',
  warning: 'vc-badge-warning',
  danger: 'vc-badge-danger',
}

export const VCBadge: React.FC<VCBadgeProps> = ({
  children,
  tone = 'default',
  className,
}) => (
  <span className={clsx('vc-badge', toneClasses[tone] || '', className)}>{children}</span>
)
