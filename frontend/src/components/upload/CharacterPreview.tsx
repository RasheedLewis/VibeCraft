import React, { useEffect, useState } from 'react'
import { apiClient } from '../../lib/apiClient'

export interface CharacterPreviewProps {
  songId: string
  className?: string
  onImageLoad?: (imageUrl: string) => void
  onError?: (error: string) => void
}

export const CharacterPreview: React.FC<CharacterPreviewProps> = ({
  songId,
  className,
  onImageLoad,
  onError,
}) => {
  const [imageUrl, setImageUrl] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchCharacterImage = async () => {
      try {
        setLoading(true)
        setError(null)

        // Fetch song details to get character image info
        const response = await apiClient.get(`/songs/${songId}`)
        const song = response.data

        if (song.character_reference_image_s3_key) {
          // Generate presigned URL for the character image
          // Note: This assumes there's an endpoint to get presigned URLs
          // If not available, we can use the image_url from the upload response
          if (song.character_image_url) {
            setImageUrl(song.character_image_url)
            onImageLoad?.(song.character_image_url)
          } else {
            // Try to get presigned URL
            try {
              const presignedResponse = await apiClient.get(
                `/songs/${songId}/character-image/url`,
              )
              if (presignedResponse.data.image_url) {
                setImageUrl(presignedResponse.data.image_url)
                onImageLoad?.(presignedResponse.data.image_url)
              } else {
                setError('Character image URL not available')
                onError?.('Character image URL not available')
              }
            } catch {
              // If presigned URL endpoint doesn't exist, that's okay
              // The image might be accessible via S3 directly or through another method
              setError('Unable to load character image')
              onError?.('Unable to load character image')
            }
          }
        } else {
          setError('No character image uploaded')
          onError?.('No character image uploaded')
        }
      } catch (err: unknown) {
        const errorMessage =
          (err as { response?: { data?: { detail?: string } } }).response?.data?.detail ||
          (err as { message?: string }).message ||
          'Failed to load character image'
        setError(errorMessage)
        onError?.(errorMessage)
      } finally {
        setLoading(false)
      }
    }

    if (songId) {
      fetchCharacterImage()
    }
  }, [songId, onImageLoad, onError])

  if (loading) {
    return (
      <div className={`flex items-center justify-center p-8 ${className || ''}`}>
        <div className="text-center">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-vc-accent-primary border-r-transparent"></div>
          <p className="mt-2 text-sm text-vc-text-secondary">
            Loading character image...
          </p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div
        className={`rounded-lg border border-vc-border/30 bg-vc-border/10 p-4 ${className || ''}`}
      >
        <p className="text-sm text-red-400">{error}</p>
      </div>
    )
  }

  if (!imageUrl) {
    return null
  }

  return (
    <div className={`character-preview ${className || ''}`}>
      <div className="rounded-lg border border-vc-border/30 bg-vc-border/10 p-4">
        <h3 className="mb-3 text-sm font-semibold text-white">
          Character Reference Image
        </h3>
        <div className="flex justify-center">
          <img
            src={imageUrl}
            alt="Character reference"
            className="max-h-64 max-w-full rounded-lg object-contain shadow-lg"
            onError={() => {
              setError('Failed to load image')
              onError?.('Failed to load image')
            }}
          />
        </div>
        {songId && (
          <p className="mt-2 text-xs text-vc-text-secondary/70">
            Character consistency enabled for this song
          </p>
        )}
      </div>
    </div>
  )
}
