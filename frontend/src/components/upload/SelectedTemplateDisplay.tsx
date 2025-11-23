import React, { useEffect, useState } from 'react'
import { apiClient } from '../../lib/apiClient'

export interface SelectedTemplateDisplayProps {
  songId: string
  className?: string
}

export const SelectedTemplateDisplay: React.FC<SelectedTemplateDisplayProps> = ({
  songId,
  className,
}) => {
  const [poseAUrl, setPoseAUrl] = useState<string | null>(null)
  const [poseBUrl, setPoseBUrl] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchImageUrls = async () => {
      try {
        setLoading(true)
        setError(null)
        const response = await apiClient.get(`/songs/${songId}/character-image/url`)
        setPoseAUrl(response.data.pose_a_url)
        setPoseBUrl(response.data.pose_b_url)
      } catch (err: unknown) {
        const errorMessage =
          (err as { response?: { data?: { detail?: string } } }).response?.data?.detail ||
          (err as { message?: string }).message ||
          'Failed to load character images'
        setError(errorMessage)
        console.error(
          '[SelectedTemplateDisplay] Failed to fetch character image URLs:',
          err,
        )
      } finally {
        setLoading(false)
      }
    }

    if (songId) {
      fetchImageUrls()
    }
  }, [songId])

  if (loading) {
    return (
      <div className={`flex items-center justify-center p-8 ${className || ''}`}>
        <div className="text-center">
          <div className="inline-block h-6 w-6 animate-spin rounded-full border-2 border-solid border-vc-accent-primary border-r-transparent"></div>
          <p className="mt-2 text-sm text-vc-text-secondary">
            Loading character images...
          </p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div
        className={`rounded-lg border border-red-500/30 bg-red-500/10 p-4 ${className || ''}`}
      >
        <p className="text-sm text-red-400">{error}</p>
      </div>
    )
  }

  if (!poseAUrl && !poseBUrl) {
    return null
  }

  return (
    <div className={`space-y-4 ${className || ''}`}>
      {/* Debug overlay - uncomment for UI testing */}
      {/* {process.env.NODE_ENV === 'development' && (
        <div className="mb-2 rounded-lg border border-yellow-500/30 bg-yellow-500/10 p-2 text-xs text-yellow-400">
          <div>Debug: {debugInfo || 'No debug info'}</div>
          <div>Loading: {loading ? 'Yes' : 'No'}</div>
          <div>Pose A URL: {poseAUrl ? 'Set' : 'Not set'}</div>
          <div>Pose B URL: {poseBUrl ? 'Set' : 'Not set'}</div>
        </div>
      )} */}
      <div className="text-center">
        <p className="text-sm text-vc-text-secondary">
          We'll use your chosen template character for video generation
        </p>
      </div>
      <div className="flex gap-4 justify-center">
        {poseAUrl && (
          <div className="flex-1 max-w-[160px]">
            <div className="aspect-square rounded-xl overflow-hidden bg-vc-border/20 border border-vc-border/30">
              <img
                src={poseAUrl}
                alt="Character Pose A"
                className="w-full h-full object-cover"
                onError={(e) => {
                  console.error('Failed to load pose A image')
                  e.currentTarget.style.display = 'none'
                }}
              />
            </div>
            <p className="mt-2 text-xs text-center text-vc-text-secondary">Pose A</p>
          </div>
        )}
        {poseBUrl && (
          <div className="flex-1 max-w-[160px]">
            <div className="aspect-square rounded-xl overflow-hidden bg-vc-border/20 border border-vc-border/30">
              <img
                src={poseBUrl}
                alt="Character Pose B"
                className="w-full h-full object-cover"
                onError={(e) => {
                  console.error('Failed to load pose B image')
                  e.currentTarget.style.display = 'none'
                }}
              />
            </div>
            <p className="mt-2 text-xs text-center text-vc-text-secondary">Pose B</p>
          </div>
        )}
      </div>
    </div>
  )
}
