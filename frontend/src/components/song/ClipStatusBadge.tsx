import React from 'react'
import clsx from 'clsx'

interface ClipStatusBadgeProps {
  status: 'queued' | 'processing' | 'completed' | 'failed' | 'canceled'
}

export const ClipStatusBadge: React.FC<ClipStatusBadgeProps> = ({ status }) => {
  const labelMap: Record<typeof status, string> = {
    queued: 'Queued',
    processing: 'Processing',
    completed: 'Completed',
    failed: 'Failed',
    canceled: 'Canceled',
  }

  const variantClass =
    status === 'completed'
      ? 'vc-badge-success'
      : status === 'failed'
        ? 'vc-badge-danger'
        : 'vc-badge'

  return (
    <span className={clsx(variantClass, 'inline-flex items-center gap-1 text-[11px]')}>
      {status === 'processing' && (
        <span className="inline-block h-2 w-2 rounded-full bg-white/80 animate-pulse" />
      )}
      {labelMap[status]}
    </span>
  )
}
