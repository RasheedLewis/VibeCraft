import React, { useState, useRef, useCallback, useEffect } from 'react'
import clsx from 'clsx'
import { apiClient } from '../../lib/apiClient'

export interface CharacterImageUploadProps {
  songId: string
  onUploadSuccess?: (imageUrl: string) => void
  onUploadError?: (error: string) => void
  onTemplateSelect?: () => void
  className?: string
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

export const CharacterImageUpload: React.FC<CharacterImageUploadProps> = ({
  songId,
  onUploadSuccess,
  onUploadError,
  onTemplateSelect,
  className,
}) => {
  const [uploading, setUploading] = useState(false)
  const [uploadingPoseB, setUploadingPoseB] = useState(false)
  const [poseAUrl, setPoseAUrl] = useState<string | null>(null)
  const [poseBUrl, setPoseBUrl] = useState<string | null>(null)
  const [selectedPose, setSelectedPose] = useState<'A' | 'B'>('A')
  const [error, setError] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const poseBInputRef = useRef<HTMLInputElement>(null)
  const [isDragging, setIsDragging] = useState(false)
  const [isDraggingPoseB, setIsDraggingPoseB] = useState(false)

  // Load existing images on mount
  useEffect(() => {
    const loadImages = async () => {
      try {
        const response = await apiClient.get(`/songs/${songId}/character-image/url`)
        if (response.data.pose_a_url) {
          setPoseAUrl(response.data.pose_a_url)
        }
        if (response.data.pose_b_url) {
          setPoseBUrl(response.data.pose_b_url)
        }
      } catch {
        // Silently fail - images may not exist yet
        console.debug('No existing character images found')
      }
    }
    if (songId) {
      loadImages()
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

  const handleFile = useCallback(
    async (file: File, isPoseB: boolean = false) => {
      const validationError = validateFile(file)
      if (validationError) {
        setError(validationError)
        onUploadError?.(validationError)
        return
      }

      setError(null)
      if (isPoseB) {
        setUploadingPoseB(true)
      } else {
        setUploading(true)
      }

      // Upload to backend
      const formData = new FormData()
      formData.append('image', file)

      try {
        const response = await apiClient.post(
          `/songs/${songId}/character-image?pose=${isPoseB ? 'B' : 'A'}`,
          formData,
          {
            headers: {
              'Content-Type': 'multipart/form-data',
            },
          },
        )

        const data = response.data
        if (isPoseB) {
          setPoseBUrl(data.image_url)
        } else {
          setPoseAUrl(data.image_url)
          onUploadSuccess?.(data.image_url)
        }
        setError(null)
      } catch (err: unknown) {
        const errorMessage =
          (err as { response?: { data?: { detail?: string }; message?: string } })
            .response?.data?.detail ||
          (err as { message?: string }).message ||
          'Upload failed'
        setError(errorMessage)
        onUploadError?.(errorMessage)
      } finally {
        if (isPoseB) {
          setUploadingPoseB(false)
        } else {
          setUploading(false)
        }
      }
    },
    [songId, onUploadSuccess, onUploadError],
  )

  const handleFileSelect = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>, isPoseB: boolean = false) => {
      const file = e.target.files?.[0]
      if (file) {
        handleFile(file, isPoseB)
      }
    },
    [handleFile],
  )

  const handleDrop = useCallback(
    (e: React.DragEvent<HTMLDivElement>, isPoseB: boolean = false) => {
      e.preventDefault()
      if (isPoseB) {
        setIsDraggingPoseB(false)
      } else {
        setIsDragging(false)
      }

      const file = e.dataTransfer.files[0]
      if (file) {
        handleFile(file, isPoseB)
      }
    },
    [handleFile],
  )

  const handleDragOver = useCallback(
    (e: React.DragEvent<HTMLDivElement>, isPoseB: boolean = false) => {
      e.preventDefault()
      if (isPoseB) {
        setIsDraggingPoseB(true)
      } else {
        setIsDragging(true)
      }
    },
    [],
  )

  const handleDragLeave = useCallback(
    (e: React.DragEvent<HTMLDivElement>, isPoseB: boolean = false) => {
      e.preventDefault()
      if (isPoseB) {
        setIsDraggingPoseB(false)
      } else {
        setIsDragging(false)
      }
    },
    [],
  )

  const handleClick = useCallback((isPoseB: boolean = false) => {
    if (isPoseB) {
      poseBInputRef.current?.click()
    } else {
      fileInputRef.current?.click()
    }
  }, [])

  const imageSize = 'w-32 h-32' // Fixed size for both images

  return (
    <div className={clsx('character-image-upload', className)}>
      <div className="flex gap-3">
        {/* Upload area for Pose A */}
        <div className="flex-1">
          <div
            className={clsx(
              'relative rounded-lg border-2 border-dashed transition-all duration-300 cursor-pointer',
              isDragging
                ? 'border-vc-accent-primary/90 shadow-vc3 bg-vc-accent-primary/10'
                : 'border-vc-border/70 hover:border-vc-accent-primary/60 hover:shadow-vc2',
              'bg-[rgba(20,20,32,0.68)]/60 backdrop-blur-xl',
              uploading && 'pointer-events-none opacity-60',
              error && 'border-red-500/50',
            )}
            onDrop={(e) => handleDrop(e, false)}
            onDragOver={(e) => handleDragOver(e, false)}
            onDragLeave={(e) => handleDragLeave(e, false)}
            onClick={() => handleClick(false)}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept="image/jpeg,image/png,image/webp"
              onChange={(e) => handleFileSelect(e, false)}
              className="hidden"
            />

            {poseAUrl ? (
              <div
                className={clsx(
                  'flex items-center justify-center rounded-xl overflow-hidden p-1',
                  imageSize,
                  selectedPose === 'A' &&
                    'ring-2 ring-vc-accent-primary/80 bg-vc-accent-primary/10',
                )}
                onClick={(e) => {
                  e.stopPropagation()
                  setSelectedPose('A')
                }}
              >
                <img
                  src={poseAUrl}
                  alt="Pose A"
                  className="w-full h-full object-cover rounded-[5px]"
                />
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center px-4 py-4 text-center">
                <svg
                  className="h-6 w-6 text-vc-accent-primary/90"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
                  />
                </svg>
                <p className="mt-2 text-sm font-medium text-white">Upload Image</p>
                <p className="mt-1 text-xs text-vc-text-secondary/70">JPEG, PNG, WEBP</p>
              </div>
            )}

            {uploading && (
              <div className="absolute inset-0 flex items-center justify-center bg-black/20 backdrop-blur-sm rounded-lg">
                <div className="text-center">
                  <div className="inline-block h-6 w-6 animate-spin rounded-full border-2 border-solid border-vc-accent-primary border-r-transparent"></div>
                </div>
              </div>
            )}
          </div>
          {poseAUrl && (
            <p className="mt-1 text-xs text-center text-vc-text-secondary">Pose A</p>
          )}
        </div>

        {/* Pose B placeholder (only shown if Pose A exists) */}
        {poseAUrl && (
          <>
            <div className="flex flex-col items-center">
              <div
                className={clsx(
                  'relative rounded-lg border-2 border-dashed transition-all duration-300 cursor-pointer',
                  imageSize,
                  isDraggingPoseB
                    ? 'border-vc-accent-primary/90 shadow-vc3 bg-vc-accent-primary/10'
                    : 'border-vc-border/40 hover:border-vc-border/60',
                  'bg-[rgba(20,20,32,0.4)]/40',
                  uploadingPoseB && 'pointer-events-none opacity-60',
                  poseBUrl &&
                    selectedPose === 'B' &&
                    'ring-2 ring-vc-accent-primary/80 bg-vc-accent-primary/10',
                )}
                onDrop={(e) => handleDrop(e, true)}
                onDragOver={(e) => handleDragOver(e, true)}
                onDragLeave={(e) => handleDragLeave(e, true)}
                onClick={() => {
                  if (poseBUrl) {
                    setSelectedPose('B')
                  } else {
                    handleClick(true)
                  }
                }}
              >
                <input
                  ref={poseBInputRef}
                  type="file"
                  accept="image/jpeg,image/png,image/webp"
                  onChange={(e) => handleFileSelect(e, true)}
                  className="hidden"
                />

                {poseBUrl ? (
                  <div
                    className={clsx(
                      'rounded-xl overflow-hidden p-1',
                      imageSize,
                      selectedPose === 'B' &&
                        'ring-2 ring-vc-accent-primary/80 bg-vc-accent-primary/10',
                    )}
                    onClick={(e) => {
                      e.stopPropagation()
                      setSelectedPose('B')
                    }}
                  >
                    <img
                      src={poseBUrl}
                      alt="Pose B"
                      className="w-full h-full object-cover rounded-[5px]"
                    />
                  </div>
                ) : (
                  <div className="flex items-center justify-center h-full">
                    <span className="text-2xl text-vc-text-muted/50">?</span>
                  </div>
                )}

                {uploadingPoseB && (
                  <div className="absolute inset-0 flex items-center justify-center bg-black/20 backdrop-blur-sm rounded-lg">
                    <div className="text-center">
                      <div className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-solid border-vc-accent-primary border-r-transparent"></div>
                    </div>
                  </div>
                )}
              </div>
              {poseBUrl && (
                <p className="mt-1 text-xs text-center text-vc-text-secondary">Pose B</p>
              )}
            </div>

            {/* Tooltip button for Pose B */}
            <div className="group relative flex items-center">
              <InfoIcon className="h-3 w-3 text-vc-text-muted hover:text-vc-text-secondary cursor-help" />
              <div className="absolute left-full top-1/2 -translate-y-1/2 ml-2 hidden group-hover:block z-10 w-64">
                <div className="bg-black/90 text-white text-xs rounded-lg px-3 py-2 shadow-lg border border-white/10">
                  <p className="text-white/80">
                    Optionally add a 'Pose B' - in the future we'll support video
                    generation with multiple images.
                  </p>
                </div>
              </div>
            </div>
          </>
        )}

        {/* Template selection button */}
        <button
          onClick={onTemplateSelect}
          disabled={uploading || uploadingPoseB}
          className="flex-1 px-4 py-4 bg-vc-border/30 text-vc-text-secondary rounded-lg hover:bg-vc-border/50 hover:text-white transition-colors disabled:opacity-50 disabled:cursor-not-allowed font-medium flex flex-col items-center justify-center"
        >
          <svg
            className="h-6 w-6 mb-2"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M4 5a1 1 0 011-1h4a1 1 0 011 1v7a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM14 5a1 1 0 011-1h4a1 1 0 011 1v7a1 1 0 01-1 1h-4a1 1 0 01-1-1V5zM4 16a1 1 0 011-1h4a1 1 0 011 1v3a1 1 0 01-1 1H5a1 1 0 01-1-1v-3zM14 16a1 1 0 011-1h4a1 1 0 011 1v3a1 1 0 01-1 1h-4a1 1 0 01-1-1v-3z"
            />
          </svg>
          <span className="text-sm">Choose Template</span>
        </button>
      </div>

      {error && <p className="mt-2 text-sm text-red-400">{error}</p>}
    </div>
  )
}
