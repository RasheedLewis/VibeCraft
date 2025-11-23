import React, { useEffect, useState, useRef, useCallback } from 'react'
import clsx from 'clsx'
import { apiClient } from '../../lib/apiClient'

export interface SelectedTemplateDisplayProps {
  songId: string
  className?: string
  disabled?: boolean
}

const MAX_FILE_SIZE_MB = 10
const ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/webp']

// Info icon component
const InfoIcon = ({ className, ...props }: React.SVGProps<SVGSVGElement>) => (
  <svg
    viewBox="0 0 24 24"
    className={className}
    fill="none"
    stroke="currentColor"
    strokeWidth={1.5}
    strokeLinecap="round"
    strokeLinejoin="round"
    {...props}
  >
    <circle cx="12" cy="12" r="10" />
    <line x1="12" y1="16" x2="12" y2="12" />
    <line x1="12" y1="8" x2="12.01" y2="8" />
  </svg>
)

export const SelectedTemplateDisplay: React.FC<SelectedTemplateDisplayProps> = ({
  songId,
  className,
  disabled = false,
}) => {
  const [poseAUrl, setPoseAUrl] = useState<string | null>(null)
  const [poseBUrl, setPoseBUrl] = useState<string | null>(null)
  const [selectedPose, setSelectedPose] = useState<'A' | 'B'>('A')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [uploadingPoseB, setUploadingPoseB] = useState(false)
  const [isDraggingPoseB, setIsDraggingPoseB] = useState(false)
  const poseBInputRef = useRef<HTMLInputElement>(null)

  // Save selected pose to backend
  const saveSelectedPose = useCallback(
    async (pose: 'A' | 'B') => {
      try {
        await apiClient.patch(`/songs/${songId}/selected-pose`, {
          selected_pose: pose,
        })
      } catch (err) {
        console.error('Failed to save selected pose:', err)
        // Don't show error to user - this is a background operation
      }
    },
    [songId],
  )

  useEffect(() => {
    const fetchImageUrls = async () => {
      try {
        setLoading(true)
        setError(null)
        const response = await apiClient.get(`/songs/${songId}/character-image/url`)
        setPoseAUrl(response.data.pose_a_url)
        setPoseBUrl(response.data.pose_b_url)
        // Load selected pose from backend, or default to Pose A if it exists
        if (response.data.selected_pose) {
          setSelectedPose(response.data.selected_pose as 'A' | 'B')
        } else if (response.data.pose_a_url) {
          setSelectedPose('A')
        } else if (response.data.pose_b_url) {
          setSelectedPose('B')
        }
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

  const validateFile = (file: File): string | null => {
    if (!ALLOWED_TYPES.includes(file.type)) {
      return 'Invalid file type. Please upload JPEG, PNG, or WEBP image.'
    }
    if (file.size > MAX_FILE_SIZE_MB * 1024 * 1024) {
      return `File size exceeds ${MAX_FILE_SIZE_MB}MB limit.`
    }
    return null
  }

  const handlePoseBUpload = useCallback(
    async (file: File) => {
      const validationError = validateFile(file)
      if (validationError) {
        setError(validationError)
        return
      }

      setError(null)
      setUploadingPoseB(true)

      // Upload to backend
      const formData = new FormData()
      formData.append('image', file)

      try {
        const response = await apiClient.post(
          `/songs/${songId}/character-image?pose=B`,
          formData,
          {
            headers: {
              'Content-Type': 'multipart/form-data',
            },
          },
        )

        const data = response.data
        setPoseBUrl(data.image_url)
        setError(null)
      } catch (err: unknown) {
        const errorMessage =
          (err as { response?: { data?: { detail?: string }; message?: string } })
            .response?.data?.detail ||
          (err as { message?: string }).message ||
          'Upload failed'
        setError(errorMessage)
      } finally {
        setUploadingPoseB(false)
      }
    },
    [songId],
  )

  const handleFileSelect = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0]
      if (file) {
        handlePoseBUpload(file)
      }
    },
    [handlePoseBUpload],
  )

  const handleDrop = useCallback(
    (e: React.DragEvent<HTMLDivElement>) => {
      e.preventDefault()
      setIsDraggingPoseB(false)

      const file = e.dataTransfer.files[0]
      if (file) {
        handlePoseBUpload(file)
      }
    },
    [handlePoseBUpload],
  )

  const handleDragOver = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    setIsDraggingPoseB(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    setIsDraggingPoseB(false)
  }, [])

  const handleClick = useCallback(() => {
    poseBInputRef.current?.click()
  }, [])

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

  const imageSize = 'w-32 h-32' // Same size as CharacterImageUpload

  return (
    <div className={`space-y-4 ${className || ''}`}>
      <div className="text-center">
        <p className="text-sm text-vc-text-secondary">
          We'll use your chosen template character for video generation
        </p>
      </div>
      <div className="flex gap-4 justify-center items-start">
        {poseAUrl && (
          <>
            <div className="flex flex-col items-center">
              <div
                className={clsx(
                  'rounded-xl bg-vc-border/20 border border-vc-border/30 transition-all overflow-hidden p-1',
                  imageSize,
                  disabled ? 'cursor-not-allowed opacity-60' : 'cursor-pointer',
                  selectedPose === 'A' &&
                    (disabled
                      ? 'ring-2 ring-vc-accent-primary/50 bg-vc-accent-primary/5 border-vc-accent-primary/30'
                      : 'ring-2 ring-vc-accent-primary/80 bg-vc-accent-primary/10 border-vc-accent-primary/50'),
                )}
                onClick={
                  disabled
                    ? undefined
                    : () => {
                        setSelectedPose('A')
                        saveSelectedPose('A')
                      }
                }
              >
                <img
                  src={poseAUrl}
                  alt="Character Pose A"
                  className="w-full h-full object-cover rounded-[5px]"
                  onError={(e) => {
                    console.error('Failed to load pose A image')
                    e.currentTarget.style.display = 'none'
                  }}
                />
              </div>
              <p className="mt-2 text-xs text-center text-vc-text-secondary">Pose A</p>
            </div>
            {/* Pose B placeholder - always show when Pose A exists */}
            <div className="flex flex-col items-center">
              {poseBUrl ? (
                <div
                  className={clsx(
                    'rounded-xl bg-vc-border/20 border border-vc-border/30 transition-all overflow-hidden p-1',
                    imageSize,
                    disabled ? 'cursor-not-allowed opacity-60' : 'cursor-pointer',
                    selectedPose === 'B' &&
                      (disabled
                        ? 'ring-2 ring-vc-accent-primary/50 bg-vc-accent-primary/5 border-vc-accent-primary/30'
                        : 'ring-2 ring-vc-accent-primary/80 bg-vc-accent-primary/10 border-vc-accent-primary/50'),
                  )}
                  onClick={
                    disabled
                      ? undefined
                      : () => {
                          setSelectedPose('B')
                          saveSelectedPose('B')
                        }
                  }
                >
                  <img
                    src={poseBUrl}
                    alt="Character Pose B"
                    className="w-full h-full object-cover rounded-[5px]"
                    onError={(e) => {
                      console.error('Failed to load pose B image')
                      e.currentTarget.style.display = 'none'
                    }}
                  />
                </div>
              ) : (
                <div
                  className={clsx(
                    'relative rounded-lg border-2 border-dashed transition-all duration-300',
                    imageSize,
                    disabled ? 'cursor-not-allowed opacity-60' : 'cursor-pointer',
                    !disabled && isDraggingPoseB
                      ? 'border-vc-accent-primary/90 shadow-vc3 bg-vc-accent-primary/10'
                      : 'border-vc-border/40',
                    !disabled && 'hover:border-vc-border/60',
                    'bg-[rgba(20,20,32,0.4)]/40',
                    uploadingPoseB && 'pointer-events-none opacity-60',
                    'flex items-center justify-center',
                  )}
                  onDrop={disabled ? undefined : handleDrop}
                  onDragOver={disabled ? undefined : handleDragOver}
                  onDragLeave={disabled ? undefined : handleDragLeave}
                  onClick={disabled ? undefined : handleClick}
                >
                  <input
                    ref={poseBInputRef}
                    type="file"
                    accept="image/jpeg,image/png,image/webp"
                    onChange={handleFileSelect}
                    className="hidden"
                  />
                  <span className="text-2xl text-vc-text-muted/50">?</span>
                  {uploadingPoseB && (
                    <div className="absolute inset-0 flex items-center justify-center bg-black/20 backdrop-blur-sm rounded-lg">
                      <div className="text-center">
                        <div className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-solid border-vc-accent-primary border-r-transparent"></div>
                      </div>
                    </div>
                  )}
                </div>
              )}
              <p className="mt-2 text-xs text-center text-vc-text-secondary">Pose B</p>
            </div>
            {/* Tooltip button for templates */}
            <div className="group relative flex items-center pt-2">
              <InfoIcon className="h-3 w-3 text-vc-text-muted hover:text-vc-text-secondary cursor-help" />
              <div className="absolute left-full top-1/2 -translate-y-1/2 ml-2 hidden group-hover:block z-10 w-64">
                <div className="bg-black/90 text-white text-xs rounded-lg px-3 py-2 shadow-lg border border-white/10">
                  <p className="text-white/60">
                    In the future we'll support video generation with multiple images.
                  </p>
                </div>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
