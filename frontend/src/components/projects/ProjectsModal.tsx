import React, { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '../../lib/apiClient'
import { useAuth } from '../../hooks/useAuth'
import { VCButton } from '../vibecraft'
import type { SongRead } from '../../types/song'

export interface ProjectsModalProps {
  isOpen: boolean
  onClose: () => void
  onOpenProject: (songId: string) => void
  onOpenAuth: () => void
}

export const ProjectsModal: React.FC<ProjectsModalProps> = ({
  isOpen,
  onClose,
  onOpenProject,
  onOpenAuth,
}) => {
  const { currentUser, isAuthenticated, logout } = useAuth()
  const queryClient = useQueryClient()
  const [deletingSongId, setDeletingSongId] = useState<string | null>(null)
  const [isDeletingAll, setIsDeletingAll] = useState(false)

  const handleLogout = () => {
    logout()
    onClose()
  }

  const handleLogin = () => {
    // Open auth modal first, then close projects modal after a brief delay
    // This prevents the visual "blink" where both modals are closed briefly
    onOpenAuth()
    // Use setTimeout to ensure AuthModal renders before ProjectsModal closes
    setTimeout(() => {
      onClose()
    }, 50)
  }

  const handleDelete = async (songId: string, e: React.MouseEvent) => {
    e.stopPropagation() // Prevent opening the project when clicking delete

    if (
      !confirm(
        'Are you sure you want to delete this project? This action cannot be undone.',
      )
    ) {
      return
    }

    setDeletingSongId(songId)
    try {
      await apiClient.delete(`/songs/${songId}`)
      // Optimistically update the cache by removing the deleted song
      queryClient.setQueryData<SongRead[]>(['songs'], (oldSongs) => {
        if (!oldSongs) return oldSongs
        return oldSongs.filter((song) => song.id !== songId)
      })
      // Also invalidate to ensure we get fresh data
      await queryClient.invalidateQueries({ queryKey: ['songs'] })
      // Refetch to ensure consistency
      await refetch()
    } catch (error) {
      console.error('Failed to delete song:', error)
      // Revert optimistic update on error
      await queryClient.invalidateQueries({ queryKey: ['songs'] })
      await refetch()
      alert('Failed to delete project. Please try again.')
    } finally {
      setDeletingSongId(null)
    }
  }

  const handleDeleteAll = async (e: React.MouseEvent) => {
    e.stopPropagation()

    if (
      !confirm(
        'Are you sure you want to delete ALL songs? This will delete all projects and un-analyzed tracks. This action cannot be undone.',
      )
    ) {
      return
    }

    setIsDeletingAll(true)
    try {
      await apiClient.delete('/songs/delete-all')
      // Clear the cache
      queryClient.setQueryData<SongRead[]>(['songs'], [])
      // Invalidate and refetch to ensure consistency
      await queryClient.invalidateQueries({ queryKey: ['songs'] })
      await refetch()
    } catch (error: unknown) {
      console.error('Failed to delete all songs:', error)
      const errorMessage =
        (error as { response?: { data?: { detail?: string } }; message?: string })
          ?.response?.data?.detail ||
        (error as { message?: string })?.message ||
        'Failed to delete all songs. Please try again.'
      await queryClient.invalidateQueries({ queryKey: ['songs'] })
      await refetch()
      alert(errorMessage)
    } finally {
      setIsDeletingAll(false)
    }
  }

  const {
    data: songs,
    isLoading,
    refetch,
  } = useQuery<SongRead[]>({
    queryKey: ['songs'],
    queryFn: async () => {
      // Backend now filters to only return songs with analysis
      const response = await apiClient.get<SongRead[]>('/songs/')
      return response.data
    },
    enabled: isAuthenticated && isOpen,
  })

  const updateAnimationsMutation = useMutation({
    mutationFn: async (animationsDisabled: boolean) => {
      const response = await apiClient.patch('/auth/me/animations', {
        animations_disabled: animationsDisabled,
      })
      return response.data
    },
    onSuccess: (data) => {
      // Update localStorage with new user info
      const userStr = localStorage.getItem('vibecraft_auth_user')
      if (userStr) {
        const user = JSON.parse(userStr)
        user.animations_disabled = data.animations_disabled
        localStorage.setItem('vibecraft_auth_user', JSON.stringify(user))
      }
      // Invalidate and refetch user query to refresh user info
      queryClient.invalidateQueries({ queryKey: ['auth', 'me'] })
      queryClient.refetchQueries({ queryKey: ['auth', 'me'] })
    },
  })

  // Close modal on Escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose()
      }
    }
    window.addEventListener('keydown', handleEscape)
    return () => window.removeEventListener('keydown', handleEscape)
  }, [isOpen, onClose])

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
          <div>
            <h2 className="text-2xl font-bold text-white mb-1">My Projects</h2>
            <p className="text-sm text-white/70">
              {currentUser?.display_name || currentUser?.email}
            </p>
          </div>
          <div className="text-white/50 text-xs italic flex-1 text-center mx-4 flex flex-col gap-1">
            <p>Projects only appear once song analysis completes.</p>
            <button
              onClick={handleDeleteAll}
              disabled={isDeletingAll}
              className="text-white/70 hover:text-white transition-colors cursor-pointer italic disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Delete all projects and un-analyzed tracks.
            </button>
            <button
              onClick={() =>
                updateAnimationsMutation.mutate(!currentUser?.animations_disabled)
              }
              disabled={updateAnimationsMutation.isPending}
              className="text-white/70 hover:text-white transition-colors cursor-pointer italic disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {currentUser?.animations_disabled
                ? 'Turn on page animations.'
                : 'Turn off page animations.'}
            </button>
          </div>
          <div className="flex gap-3">
            {isAuthenticated ? (
              <VCButton variant="secondary" onClick={handleLogout}>
                Logout
              </VCButton>
            ) : (
              <VCButton onClick={handleLogin}>Login</VCButton>
            )}
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
        </div>

        {/* Content */}
        {isLoading ? (
          <div className="text-white/70 text-center py-12">Loading projects...</div>
        ) : songs && songs.length > 0 ? (
          <div className="flex flex-col gap-3">
            {songs.map((song) => (
              <div
                key={song.id}
                onClick={() => {
                  onOpenProject(song.id)
                  onClose()
                }}
                className="relative w-full bg-white/10 backdrop-blur-lg rounded-xl p-3 border border-white/20 hover:bg-white/20 transition-all cursor-pointer"
              >
                <button
                  onClick={(e) => handleDelete(song.id, e)}
                  disabled={deletingSongId === song.id}
                  className="absolute top-2 right-2 text-white/50 hover:text-white transition-colors p-1 hover:bg-white/20 rounded z-10 disabled:opacity-50"
                  aria-label="Delete project"
                >
                  <svg
                    className="w-4 h-4"
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
                <h3 className="text-lg font-semibold text-white mb-1 pr-8">
                  {song.title || 'Untitled Song'}
                </h3>
                <p className="text-white/70 text-sm mb-1">{song.original_filename}</p>
                <div className="flex items-center gap-3">
                  {(song.composed_video_duration_sec ?? song.duration_sec) && (
                    <p className="text-white/50 text-xs">
                      {Math.round(
                        song.composed_video_duration_sec ?? song.duration_sec ?? 0,
                      )}
                      s
                    </p>
                  )}
                  {song.composed_video_s3_key && (
                    <div className="text-green-400 text-xs">✓ Video composed</div>
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-12">
            <p className="text-white/70">No projects yet. Create your first one!</p>
          </div>
        )}

        {songs && songs.length >= 5 && (
          <div className="mt-8 p-4 bg-yellow-500/20 border border-yellow-500/50 rounded-lg text-yellow-200 text-sm text-center">
            You've reached the maximum of 5 projects. Delete an existing project to create
            a new one.
          </div>
        )}
      </div>
    </div>
  )
}
