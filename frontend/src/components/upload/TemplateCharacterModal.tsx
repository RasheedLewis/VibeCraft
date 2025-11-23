import React, { useEffect, useState } from 'react'
import clsx from 'clsx'
import { apiClient } from '../../lib/apiClient'

export interface TemplateCharacter {
  id: string
  name: string
  description?: string
  poses: Array<{
    id: string
    thumbnail_url: string
    image_url: string
  }>
  default_pose: string
}

export interface TemplateCharacterModalProps {
  isOpen: boolean
  onClose: () => void
  onSelect: (characterId: string) => void
  songId: string
}

export const TemplateCharacterModal: React.FC<TemplateCharacterModalProps> = ({
  isOpen,
  onClose,
  onSelect,
  songId,
}) => {
  const [templates, setTemplates] = useState<TemplateCharacter[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [selectedCharacterId, setSelectedCharacterId] = useState<string | null>(null)
  const [applying, setApplying] = useState(false)

  useEffect(() => {
    if (isOpen) {
      fetchTemplates()
    }
  }, [isOpen])

  const fetchTemplates = async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await apiClient.get('/template-characters')
      setTemplates(response.data.templates || [])
    } catch (err: unknown) {
      const errorMessage =
        (err as { response?: { data?: { detail?: string } } }).response?.data?.detail ||
        (err as { message?: string }).message ||
        'Failed to load template characters'
      setError(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  const handleSelect = async (characterId: string) => {
    setSelectedCharacterId(characterId)
    setApplying(true)
    setError(null)

    try {
      await apiClient.post(`/songs/${songId}/character-image/template`, {
        character_id: characterId,
      })
      onSelect(characterId)
      onClose()
    } catch (err: unknown) {
      const errorMessage =
        (err as { response?: { data?: { detail?: string } } }).response?.data?.detail ||
        (err as { message?: string }).message ||
        'Failed to apply template character'
      setError(errorMessage)
    } finally {
      setApplying(false)
      setSelectedCharacterId(null)
    }
  }

  if (!isOpen) return null

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="relative w-full max-w-4xl rounded-2xl bg-[rgba(20,20,32,0.95)] backdrop-blur-xl border border-vc-border/50 shadow-2xl p-6 max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold text-white">Choose Template Character</h2>
          <button
            onClick={onClose}
            className="text-vc-text-secondary hover:text-white transition-colors p-2 hover:bg-vc-border/30 rounded-lg"
            aria-label="Close"
          >
            <svg
              className="w-6 h-6"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>

        {/* Content */}
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-vc-accent-primary border-r-transparent"></div>
            <p className="ml-3 text-vc-text-secondary">Loading templates...</p>
          </div>
        ) : error ? (
          <div className="py-12 text-center">
            <p className="text-red-400">{error}</p>
            <button
              onClick={fetchTemplates}
              className="mt-4 px-4 py-2 bg-vc-accent-primary text-white rounded-lg hover:bg-vc-accent-primary/90 transition-colors"
            >
              Retry
            </button>
          </div>
        ) : templates.length === 0 ? (
          <div className="py-12 text-center text-vc-text-secondary">
            No template characters available
          </div>
        ) : (
          <>
            <p className="text-sm text-vc-text-secondary mb-6">
              Select a character (each shows 2 poses):
            </p>
            <div className="grid grid-cols-4 gap-4">
              {templates.map((template) => {
                const poseA = template.poses.find((p) => p.id === 'pose-a')
                const poseB = template.poses.find((p) => p.id === 'pose-b')
                const isSelected = selectedCharacterId === template.id
                const isApplying = applying && isSelected

                return (
                  <div
                    key={template.id}
                    className={clsx(
                      'relative rounded-xl border-2 transition-all cursor-pointer',
                      isSelected
                        ? 'border-vc-accent-primary shadow-lg shadow-vc-accent-primary/20'
                        : 'border-vc-border/50 hover:border-vc-accent-primary/60 hover:shadow-md',
                      'bg-[rgba(20,20,32,0.8)] overflow-hidden',
                      isApplying && 'pointer-events-none opacity-60',
                    )}
                    onClick={() => !applying && handleSelect(template.id)}
                  >
                    {/* Poses stacked vertically */}
                    <div className="flex flex-col">
                      {poseA && (
                        <div className="w-full aspect-square overflow-hidden bg-vc-border/20">
                          <img
                            src={poseA.thumbnail_url}
                            alt={`${template.name} - Pose A`}
                            className="w-full h-full object-cover"
                            onError={(e) => {
                              // If S3 image fails, try to load from local public directory
                              const img = e.currentTarget
                              const characterNum = template.id.split('-')[1]
                              const localPath = `/img/characters/character${characterNum}-pose1.png`
                              if (img.src !== localPath) {
                                img.src = localPath
                              } else {
                                // If local also fails, show placeholder
                                img.style.display = 'none'
                                img.parentElement!.innerHTML = `
                                  <div class="w-full h-full flex items-center justify-center text-vc-text-muted text-xs">
                                    Image not available
                                  </div>
                                `
                              }
                            }}
                          />
                        </div>
                      )}
                      {poseB && (
                        <div className="w-full aspect-square overflow-hidden bg-vc-border/20 border-t border-vc-border/30">
                          <img
                            src={poseB.thumbnail_url}
                            alt={`${template.name} - Pose B`}
                            className="w-full h-full object-cover"
                            onError={(e) => {
                              // If S3 image fails, try to load from local public directory
                              const img = e.currentTarget
                              const characterNum = template.id.split('-')[1]
                              const localPath = `/img/characters/character${characterNum}-pose2.png`
                              if (img.src !== localPath) {
                                img.src = localPath
                              } else {
                                // If local also fails, show placeholder
                                img.style.display = 'none'
                                img.parentElement!.innerHTML = `
                                  <div class="w-full h-full flex items-center justify-center text-vc-text-muted text-xs">
                                    Image not available
                                  </div>
                                `
                              }
                            }}
                          />
                        </div>
                      )}
                    </div>

                    {/* Character name */}
                    <div className="p-3 bg-[rgba(20,20,32,0.95)]">
                      <h3 className="text-sm font-semibold text-white text-center">
                        {template.name}
                      </h3>
                      {template.description && (
                        <p className="text-xs text-vc-text-secondary text-center mt-1">
                          {template.description}
                        </p>
                      )}
                    </div>

                    {/* Loading overlay */}
                    {isApplying && (
                      <div className="absolute inset-0 flex items-center justify-center bg-black/40 backdrop-blur-sm">
                        <div className="inline-block h-6 w-6 animate-spin rounded-full border-2 border-solid border-vc-accent-primary border-r-transparent"></div>
                      </div>
                    )}
                  </div>
                )
              })}
            </div>

            {error && (
              <div className="mt-4 p-3 bg-red-500/10 border border-red-500/30 rounded-lg">
                <p className="text-sm text-red-400">{error}</p>
              </div>
            )}
          </>
        )}

        {/* Footer */}
        <div className="mt-6 flex justify-end">
          <button
            onClick={onClose}
            className="px-6 py-2 bg-vc-border/30 text-vc-text-secondary rounded-lg hover:bg-vc-border/50 hover:text-white transition-colors"
            disabled={applying}
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  )
}
