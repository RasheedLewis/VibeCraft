import React from 'react'
import clsx from 'clsx'

interface VCCardProps extends React.HTMLAttributes<HTMLDivElement> {
  padded?: boolean
}

export const VCCard: React.FC<VCCardProps> = ({
  padded = true,
  className,
  children,
  ...rest
}) => (
  <div className={clsx(padded ? 'vc-card' : 'vc-card-tight', className)} {...rest}>
    {children}
  </div>
)
