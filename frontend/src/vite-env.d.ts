/// <reference types="vite/client" />

// Build-time replacement for development API URL
// This is replaced by Vite's define config, so it never appears in production bundles
// In production: becomes null
// In development: becomes the localhost URL string
declare const __DEV_DEFAULT_API__: string | null
