import React, { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { apiClient } from '../lib/apiClient'
import { useAuth } from '../hooks/useAuth'
import { VCButton } from '../components/vibecraft'
import type { SongRead } from '../types/song'

export const ProjectsPage: React.FC = () => {
  const navigate = useNavigate()
  const { currentUser, isAuthenticated, logout } = useAuth()

  const { data: songs, isLoading } = useQuery<SongRead[]>({
    queryKey: ['songs'],
    queryFn: async () => {
      const response = await apiClient.get<SongRead[]>('/songs/')
      return response.data
    },
    enabled: isAuthenticated,
  })

  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/login')
    }
  }, [isAuthenticated, navigate])

  const handleCreateNew = () => {
    navigate('/')
  }

  const handleOpenProject = (songId: string) => {
    navigate(`/?songId=${songId}`)
  }

  if (!isAuthenticated) {
    return null
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900">
      <div className="container mx-auto px-4 py-8">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-4xl font-bold text-white mb-2">My Projects</h1>
            <p className="text-white/70">
              {currentUser?.display_name || currentUser?.email}
            </p>
          </div>
          <div className="flex gap-4">
            <VCButton onClick={handleCreateNew}>Create New</VCButton>
            <VCButton variant="secondary" onClick={logout}>
              Logout
            </VCButton>
          </div>
        </div>

        {isLoading ? (
          <div className="text-white/70 text-center py-12">Loading projects...</div>
        ) : songs && songs.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {songs.map((song) => (
              <div
                key={song.id}
                onClick={() => handleOpenProject(song.id)}
                className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/20 hover:bg-white/20 transition-all cursor-pointer"
              >
                <h3 className="text-xl font-semibold text-white mb-2">
                  {song.title || 'Untitled Song'}
                </h3>
                <p className="text-white/70 text-sm mb-4">{song.original_filename}</p>
                {song.duration_sec && (
                  <p className="text-white/50 text-xs">
                    {Math.round(song.duration_sec)}s
                  </p>
                )}
                {song.composed_video_s3_key && (
                  <div className="mt-4 text-green-400 text-sm">✓ Video composed</div>
                )}
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-12">
            <p className="text-white/70 mb-6">No projects yet. Create your first one!</p>
            <VCButton onClick={handleCreateNew}>Create New Project</VCButton>
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
