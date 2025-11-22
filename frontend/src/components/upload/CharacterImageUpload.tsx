import React, { useState, useRef, useCallback } from 'react'
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

export const CharacterImageUpload: React.FC<CharacterImageUploadProps> = ({
  songId,
  onUploadSuccess,
  onUploadError,
  onTemplateSelect,
  className,
}) => {
  const [uploading, setUploading] = useState(false)
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [isDragging, setIsDragging] = useState(false)

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
    async (file: File) => {
      const validationError = validateFile(file)
      if (validationError) {
        setError(validationError)
        onUploadError?.(validationError)
        return
      }

      setError(null)
      setUploading(true)

      // Create preview
      const reader = new FileReader()
      reader.onload = (e) => {
        setPreviewUrl(e.target?.result as string)
      }
      reader.readAsDataURL(file)

      // Upload to backend
      const formData = new FormData()
      formData.append('image', file)

      try {
        const response = await apiClient.post(
          `/songs/${songId}/character-image`,
          formData,
          {
            headers: {
              'Content-Type': 'multipart/form-data',
            },
          },
        )

        const data = response.data
        onUploadSuccess?.(data.image_url)
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
        setUploading(false)
      }
    },
    [songId, onUploadSuccess, onUploadError],
  )

  const handleFileSelect = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0]
      if (file) {
        handleFile(file)
      }
    },
    [handleFile],
  )

  const handleDrop = useCallback(
    (e: React.DragEvent<HTMLDivElement>) => {
      e.preventDefault()
      setIsDragging(false)

      const file = e.dataTransfer.files[0]
      if (file) {
        handleFile(file)
      }
    },
    [handleFile],
  )

  const handleDragOver = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    setIsDragging(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    setIsDragging(false)
  }, [])

  const handleClick = useCallback(() => {
    fileInputRef.current?.click()
  }, [])

  return (
    <div className={clsx('character-image-upload', className)}>
      <div
        className={clsx(
          'relative rounded-2xl border-2 border-dashed transition-all duration-300',
          isDragging
            ? 'border-vc-accent-primary/90 shadow-vc3 bg-vc-accent-primary/10'
            : 'border-vc-border/70 hover:border-vc-accent-primary/60 hover:shadow-vc2',
          'bg-[rgba(20,20,32,0.68)]/60 backdrop-blur-xl',
          uploading && 'pointer-events-none opacity-60',
          error && 'border-red-500/50',
        )}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onClick={handleClick}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept="image/jpeg,image/png,image/webp"
          onChange={handleFileSelect}
          className="hidden"
        />

        {previewUrl ? (
          <div className="flex flex-col items-center justify-center p-8">
            <img
              src={previewUrl}
              alt="Character preview"
              className="max-h-64 max-w-full rounded-lg object-contain shadow-lg"
            />
            <p className="mt-4 text-sm text-vc-text-secondary">
              Click or drag to replace image
            </p>
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center px-10 py-12 text-center">
            <svg
              className="h-12 w-12 text-vc-accent-primary/90"
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
            <h3 className="mt-4 text-lg font-semibold text-white">
              Upload Character Image
            </h3>
            <p className="mt-2 text-sm text-vc-text-secondary">
              Drag & drop character image here, or click to select
            </p>
            <p className="mt-1 text-xs text-vc-text-secondary/70">
              JPEG, PNG, or WEBP (max {MAX_FILE_SIZE_MB}MB)
            </p>
          </div>
        )}

        {uploading && (
          <div className="absolute inset-0 flex items-center justify-center bg-black/20 backdrop-blur-sm rounded-2xl">
            <div className="text-center">
              <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-vc-accent-primary border-r-transparent"></div>
              <p className="mt-2 text-sm text-white">Uploading...</p>
            </div>
          </div>
        )}
      </div>

      {error && <p className="mt-2 text-sm text-red-400">{error}</p>}

      {/* Template selection button */}
      <div className="mt-4 flex items-center gap-4">
        <div className="flex-1 border-t border-vc-border/30"></div>
        <span className="text-xs text-vc-text-secondary/70">OR</span>
        <div className="flex-1 border-t border-vc-border/30"></div>
      </div>
      <button
        onClick={onTemplateSelect}
        disabled={uploading}
        className="mt-4 w-full px-4 py-3 bg-vc-border/30 text-vc-text-secondary rounded-lg hover:bg-vc-border/50 hover:text-white transition-colors disabled:opacity-50 disabled:cursor-not-allowed font-medium"
      >
        Choose Template
      </button>
    </div>
  )
}
