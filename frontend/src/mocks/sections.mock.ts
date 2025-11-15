/**
 * Mock section data for Person B's development
 * Use this in PR-08 and PR-09 until Person A completes PR-04
 */

export type SongSectionType =
  | 'intro'
  | 'verse'
  | 'pre_chorus'
  | 'chorus'
  | 'bridge'
  | 'drop'
  | 'solo'
  | 'outro'
  | 'other'

export interface SongSection {
  id: string
  type: SongSectionType
  startSec: number
  endSec: number
  confidence: number
  repetitionGroup?: string
}

/**
 * Sample 1: Electronic/EDM track (~3:30)
 * Typical structure: Intro → Verse → Chorus → Verse → Chorus → Bridge → Chorus → Outro
 */
export const mockSectionsElectronic: SongSection[] = [
  {
    id: 'section-1',
    type: 'intro',
    startSec: 0,
    endSec: 16,
    confidence: 0.95,
  },
  {
    id: 'section-2',
    type: 'verse',
    startSec: 16,
    endSec: 48,
    confidence: 0.92,
    repetitionGroup: 'verse-1',
  },
  {
    id: 'section-3',
    type: 'pre_chorus',
    startSec: 48,
    endSec: 64,
    confidence: 0.88,
  },
  {
    id: 'section-4',
    type: 'chorus',
    startSec: 64,
    endSec: 96,
    confidence: 0.98,
    repetitionGroup: 'chorus-1',
  },
  {
    id: 'section-5',
    type: 'verse',
    startSec: 96,
    endSec: 128,
    confidence: 0.91,
    repetitionGroup: 'verse-2',
  },
  {
    id: 'section-6',
    type: 'pre_chorus',
    startSec: 128,
    endSec: 144,
    confidence: 0.87,
  },
  {
    id: 'section-7',
    type: 'chorus',
    startSec: 144,
    endSec: 176,
    confidence: 0.97,
    repetitionGroup: 'chorus-2',
  },
  {
    id: 'section-8',
    type: 'bridge',
    startSec: 176,
    endSec: 200,
    confidence: 0.85,
  },
  {
    id: 'section-9',
    type: 'chorus',
    startSec: 200,
    endSec: 232,
    confidence: 0.96,
    repetitionGroup: 'chorus-3',
  },
  {
    id: 'section-10',
    type: 'outro',
    startSec: 232,
    endSec: 250,
    confidence: 0.93,
  },
]

/**
 * Sample 2: Pop/Rock track (~4:00)
 * Typical structure: Intro → Verse → Chorus → Verse → Chorus → Solo → Chorus → Outro
 */
export const mockSectionsPopRock: SongSection[] = [
  {
    id: 'section-1',
    type: 'intro',
    startSec: 0,
    endSec: 20,
    confidence: 0.94,
  },
  {
    id: 'section-2',
    type: 'verse',
    startSec: 20,
    endSec: 52,
    confidence: 0.93,
    repetitionGroup: 'verse-1',
  },
  {
    id: 'section-3',
    type: 'chorus',
    startSec: 52,
    endSec: 84,
    confidence: 0.97,
    repetitionGroup: 'chorus-1',
  },
  {
    id: 'section-4',
    type: 'verse',
    startSec: 84,
    endSec: 116,
    confidence: 0.92,
    repetitionGroup: 'verse-2',
  },
  {
    id: 'section-5',
    type: 'chorus',
    startSec: 116,
    endSec: 148,
    confidence: 0.98,
    repetitionGroup: 'chorus-2',
  },
  {
    id: 'section-6',
    type: 'solo',
    startSec: 148,
    endSec: 180,
    confidence: 0.89,
  },
  {
    id: 'section-7',
    type: 'chorus',
    startSec: 180,
    endSec: 212,
    confidence: 0.96,
    repetitionGroup: 'chorus-3',
  },
  {
    id: 'section-8',
    type: 'outro',
    startSec: 212,
    endSec: 240,
    confidence: 0.91,
  },
]

/**
 * Sample 3: Hip-Hop track (~3:15)
 * Typical structure: Intro → Verse → Hook → Verse → Hook → Bridge → Hook → Outro
 */
export const mockSectionsHipHop: SongSection[] = [
  {
    id: 'section-1',
    type: 'intro',
    startSec: 0,
    endSec: 12,
    confidence: 0.96,
  },
  {
    id: 'section-2',
    type: 'verse',
    startSec: 12,
    endSec: 48,
    confidence: 0.94,
    repetitionGroup: 'verse-1',
  },
  {
    id: 'section-3',
    type: 'chorus',
    startSec: 48,
    endSec: 72,
    confidence: 0.99,
    repetitionGroup: 'hook-1',
  },
  {
    id: 'section-4',
    type: 'verse',
    startSec: 72,
    endSec: 108,
    confidence: 0.93,
    repetitionGroup: 'verse-2',
  },
  {
    id: 'section-5',
    type: 'chorus',
    startSec: 108,
    endSec: 132,
    confidence: 0.98,
    repetitionGroup: 'hook-2',
  },
  {
    id: 'section-6',
    type: 'bridge',
    startSec: 132,
    endSec: 156,
    confidence: 0.87,
  },
  {
    id: 'section-7',
    type: 'chorus',
    startSec: 156,
    endSec: 180,
    confidence: 0.97,
    repetitionGroup: 'hook-3',
  },
  {
    id: 'section-8',
    type: 'outro',
    startSec: 180,
    endSec: 195,
    confidence: 0.92,
  },
]

/**
 * Default export - use the electronic track as default
 */
export const mockSections = mockSectionsElectronic

/**
 * Helper to get sections for a specific song ID
 */
export function getMockSections(songId: string): SongSection[] {
  // In real implementation, this would fetch from API
  // For now, return mock data based on song ID pattern
  if (songId.includes('electronic') || songId.includes('edm')) {
    return mockSectionsElectronic
  }
  if (songId.includes('pop') || songId.includes('rock')) {
    return mockSectionsPopRock
  }
  if (songId.includes('hiphop') || songId.includes('rap')) {
    return mockSectionsHipHop
  }
  return mockSections // default
}
