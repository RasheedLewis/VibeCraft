export const normalizeJobStatus = (
  status?: string,
): 'queued' | 'processing' | 'completed' | 'failed' => {
  const normalized = status?.toLowerCase()
  if (normalized === 'processing') return 'processing'
  if (normalized === 'completed') return 'completed'
  if (normalized === 'failed') return 'failed'
  return 'queued'
}

export const normalizeClipStatus = (
  status?: string,
): 'queued' | 'processing' | 'completed' | 'failed' | 'canceled' => {
  const normalized = status?.toLowerCase()
  if (normalized === 'processing' || normalized === 'generating') return 'processing'
  if (normalized === 'completed' || normalized === 'done') return 'completed'
  if (normalized === 'failed' || normalized === 'error') return 'failed'
  if (normalized === 'canceled' || normalized === 'cancelled') return 'canceled'
  return 'queued'
}
