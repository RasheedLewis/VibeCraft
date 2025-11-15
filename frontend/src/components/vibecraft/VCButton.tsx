import React from 'react'
import clsx from 'clsx'

type VCButtonVariant = 'primary' | 'secondary' | 'ghost'
type VCButtonSize = 'sm' | 'md' | 'lg'

export interface VCButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: VCButtonVariant
  size?: VCButtonSize
  iconLeft?: React.ReactNode
  iconRight?: React.ReactNode
  loading?: boolean
}

const variantClasses: Record<VCButtonVariant, string> = {
  primary: 'vc-btn-primary',
  secondary: 'vc-btn-secondary',
  ghost: 'vc-btn-ghost',
}

const sizeClasses: Record<VCButtonSize, string> = {
  sm: 'vc-btn-sm',
  md: '',
  lg: 'h-12 px-6 text-base',
}

export const VCButton: React.FC<VCButtonProps> = ({
  variant = 'primary',
  size = 'md',
  iconLeft,
  iconRight,
  loading,
  children,
  className,
  disabled,
  ...rest
}) => {
  return (
    <button
      className={clsx('vc-btn', variantClasses[variant], sizeClasses[size], className)}
      disabled={loading || disabled}
      {...rest}
    >
      {loading && (
        <span className="inline-flex h-2.5 w-2.5 rounded-full bg-vc-accent-tertiary vc-pulse-animate" />
      )}
      {iconLeft && <span className="-ml-1 flex items-center">{iconLeft}</span>}
      <span>{children}</span>
      {iconRight && <span className="-mr-1 flex items-center">{iconRight}</span>}
    </button>
  )
}
