import React from 'react'
import clsx from 'clsx'

interface VCIconButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  selected?: boolean
}

export const VCIconButton: React.FC<VCIconButtonProps> = ({
  className,
  selected,
  children,
  ...rest
}) => (
  <button
    className={clsx(selected ? 'vc-icon-btn-selected' : 'vc-icon-btn', className)}
    {...rest}
  >
    {children}
  </button>
)
