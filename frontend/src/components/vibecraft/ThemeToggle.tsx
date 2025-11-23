import React from 'react'
import clsx from 'clsx'

import { useTheme } from '../../hooks/useTheme'
import { VCIconButton } from './VCIconButton'

const ICON_MAP: Record<'dark' | 'light' | 'system', string> = {
  dark: '🌙',
  light: '☀️',
  system: '🌓',
}

const LABEL_MAP: Record<'dark' | 'light' | 'system', string> = {
  dark: 'Dark mode',
  light: 'Light mode',
  system: 'System theme',
}

const NEXT_MAP: Record<'dark' | 'light' | 'system', 'dark' | 'light' | 'system'> = {
  dark: 'light',
  light: 'system',
  system: 'dark',
}

export const ThemeToggle: React.FC = () => {
  const { theme, resolvedTheme, setTheme } = useTheme()

  const handleToggle = () => {
    const next = NEXT_MAP[theme]
    setTheme(next)
  }

  return (
    <VCIconButton
      aria-label={`Switch theme (currently ${LABEL_MAP[resolvedTheme]})`}
      title={`Theme: ${LABEL_MAP[resolvedTheme]} (click to change)`}
      className={clsx(
        'h-10 w-10 text-base',
        theme === 'system' && 'ring-1 ring-vc-border/40 dark:ring-vc-border/60',
      )}
      onClick={handleToggle}
    >
      <span aria-hidden>{ICON_MAP[resolvedTheme]}</span>
    </VCIconButton>
  )
}
