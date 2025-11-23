import React, { useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
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

  const handleLogout = () => {
    logout()
    onClose()
  }

  const handleLogin = () => {
    onClose()
    onOpenAuth()
  }

  const { data: songs, isLoading } = useQuery<SongRead[]>({
    queryKey: ['songs'],
    queryFn: async () => {
      const response = await apiClient.get<SongRead[]>('/songs/')
      const allSongs = response.data
      
      // Filter to only show songs with complete analysis
      // Check if analysis exists for each song by attempting to fetch it
      const songsWithAnalysis = await Promise.allSettled(
        allSongs.map(async (song) => {
          try {
            await apiClient.get(`/songs/${song.id}/analysis`)
            return song
          } catch {
            return null
          }
        })
      )
      
      // Return only songs where analysis fetch succeeded
      return songsWithAnalysis
        .map((result) => (result.status === 'fulfilled' ? result.value : null))
        .filter((song): song is SongRead => song !== null)
    },
    enabled: isAuthenticated && isOpen,
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
                className="w-full bg-white/10 backdrop-blur-lg rounded-xl p-3 border border-white/20 hover:bg-white/20 transition-all cursor-pointer"
              >
                <h3 className="text-lg font-semibold text-white mb-1">
                  {song.title || 'Untitled Song'}
                </h3>
                <p className="text-white/70 text-sm mb-1">{song.original_filename}</p>
                <div className="flex items-center gap-3">
                  {song.duration_sec && (
                    <p className="text-white/50 text-xs">
                      {Math.round(song.duration_sec)}s
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
