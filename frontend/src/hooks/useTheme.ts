import { useCallback, useEffect, useState } from 'react'

type ThemeMode = 'dark' | 'light' | 'system'

const STORAGE_KEY = 'vc-theme'
const CLASS_DARK = 'dark'
const CLASS_LIGHT = 'light'

const getStoredTheme = (): ThemeMode => {
  if (typeof window === 'undefined') return 'system'
  const value = window.localStorage.getItem(STORAGE_KEY) as ThemeMode | null
  if (value === 'dark' || value === 'light' || value === 'system') {
    return value
  }
  return 'system'
}

const prefersDark = (): boolean =>
  typeof window !== 'undefined' &&
  window.matchMedia &&
  window.matchMedia('(prefers-color-scheme: dark)').matches

const applyThemeClass = (mode: ThemeMode) => {
  const root = document.documentElement
  root.classList.remove(CLASS_DARK, CLASS_LIGHT)

  if (mode === 'dark') {
    root.classList.add(CLASS_DARK)
  } else if (mode === 'light') {
    root.classList.add(CLASS_LIGHT)
  } else {
    // system: mirror current OS preference
    root.classList.add(prefersDark() ? CLASS_DARK : CLASS_LIGHT)
  }
}

export const useTheme = () => {
  const [theme, setTheme] = useState<ThemeMode>(() => getStoredTheme())

  const updateTheme = useCallback(
    (mode: ThemeMode) => {
      setTheme(mode)
      if (typeof window !== 'undefined') {
        window.localStorage.setItem(STORAGE_KEY, mode)
      }
    },
    [setTheme],
  )

  useEffect(() => {
    if (typeof window === 'undefined') return
    applyThemeClass(theme)
  }, [theme])

  useEffect(() => {
    if (typeof window === 'undefined' || theme !== 'system') return
    const media = window.matchMedia('(prefers-color-scheme: dark)')
    const handler = (event: MediaQueryListEvent) => {
      const root = document.documentElement
      root.classList.remove(CLASS_DARK, CLASS_LIGHT)
      root.classList.add(event.matches ? CLASS_DARK : CLASS_LIGHT)
    }
    media.addEventListener('change', handler)
    return () => media.removeEventListener('change', handler)
  }, [theme])

  const resolvedTheme: ThemeMode =
    theme === 'system' ? (prefersDark() ? 'dark' : 'light') : theme

  return {
    theme,
    resolvedTheme,
    setTheme: updateTheme,
  }
}
