/** Songs API functions for uploading and managing audio files. */

import { apiRequest, getAuthToken } from './client';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export interface Song {
  id: string;
  user_id: string;
  title: string;
  duration_sec: number;
  audio_s3_key: string;
  created_at: string;
}

export interface SongUploadResponse {
  id: string;
  status: string;
}

/**
 * Upload an audio file to the server.
 * @param file - The audio file to upload
 * @param onProgress - Optional callback for upload progress (0-100)
 * @returns Promise resolving to the uploaded song response
 */
export async function uploadSong(
  file: File,
  onProgress?: (progress: number) => void
): Promise<SongUploadResponse> {
  const token = getAuthToken();
  if (!token) {
    throw new Error('Authentication required');
  }

  const formData = new FormData();
  formData.append('file', file);

  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();

    // Track upload progress
    if (onProgress) {
      xhr.upload.addEventListener('progress', (event) => {
        if (event.lengthComputable) {
          const progress = Math.round((event.loaded / event.total) * 100);
          onProgress(progress);
        }
      });
    }

    xhr.addEventListener('load', () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          const response = JSON.parse(xhr.responseText);
          resolve(response);
        } catch {
          reject(new Error('Invalid response from server'));
        }
      } else {
        try {
          const error = JSON.parse(xhr.responseText);
          reject(new Error(error.detail || `Upload failed with status ${xhr.status}`));
        } catch {
          reject(new Error(`Upload failed with status ${xhr.status}`));
        }
      }
    });

    xhr.addEventListener('error', () => {
      reject(new Error('Network error during upload'));
    });

    xhr.addEventListener('abort', () => {
      reject(new Error('Upload was cancelled'));
    });

    const url = `${API_BASE_URL}/api/v1/songs`;
    xhr.open('POST', url);
    xhr.setRequestHeader('Authorization', `Bearer ${token}`);
    xhr.send(formData);
  });
}

/**
 * Get song details by ID.
 * @param songId - The song ID
 * @returns Promise resolving to the song details
 */
export async function getSong(songId: string): Promise<Song> {
  return apiRequest<Song>(`/api/v1/songs/${songId}`);
}

/**
 * List all songs for the current user.
 * @returns Promise resolving to an array of songs
 */
export async function listSongs(): Promise<Song[]> {
  return apiRequest<Song[]>('/api/v1/songs');
}

