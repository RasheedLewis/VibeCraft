"""Analysis schemas for song analysis results."""

from typing import List, Literal, Optional

from pydantic import BaseModel, Field

SongSectionType = Literal[
    "intro",
    "verse",
    "pre_chorus",
    "chorus",
    "bridge",
    "drop",
    "solo",
    "outro",
    "other",
]


class SongSection(BaseModel):
    """Represents a structural section of a song."""

    id: str
    type: SongSectionType
    type_soft: Optional[str] = Field(None, alias="typeSoft")
    display_name: Optional[str] = Field(None, alias="displayName")
    raw_label: Optional[int] = Field(None, alias="rawLabel")
    start_sec: float = Field(..., alias="startSec")
    end_sec: float = Field(..., alias="endSec")
    confidence: float
    repetition_group: Optional[str] = Field(None, alias="repetitionGroup")

    model_config = {"populate_by_name": True}


class MoodVector(BaseModel):
    """Mood vector representing emotional characteristics of a song."""

    energy: float = Field(..., ge=0.0, le=1.0, description="Energy level (0-1)")
    valence: float = Field(..., ge=0.0, le=1.0, description="Positivity/happiness (0-1)")
    danceability: float = Field(..., ge=0.0, le=1.0, description="Danceability (0-1)")
    tension: float = Field(..., ge=0.0, le=1.0, description="Tension/intensity (0-1)")


class SectionLyrics(BaseModel):
    """Lyrics for a specific section of a song."""

    section_id: str = Field(..., alias="sectionId")
    start_sec: float = Field(..., alias="startSec")
    end_sec: float = Field(..., alias="endSec")
    text: str

    model_config = {"populate_by_name": True}


class SongAnalysis(BaseModel):
    """Complete song analysis results."""

    duration_sec: float = Field(..., alias="durationSec")
    bpm: Optional[float] = None
    beat_times: list[float] = Field(default_factory=list, alias="beatTimes")
    sections: List[SongSection] = []
    mood_primary: str = Field(..., alias="moodPrimary")
    mood_tags: List[str] = Field(default_factory=list, alias="moodTags")
    mood_vector: MoodVector = Field(..., alias="moodVector")
    primary_genre: Optional[str] = Field(None, alias="primaryGenre")
    sub_genres: Optional[List[str]] = Field(None, alias="subGenres")
    lyrics_available: bool = Field(False, alias="lyricsAvailable")
    section_lyrics: Optional[List[SectionLyrics]] = Field(None, alias="sectionLyrics")

    model_config = {"populate_by_name": True}


class ClipBoundaryMetadata(BaseModel):
    """Metadata for a single clip boundary with beat alignment information."""

    start_time: float = Field(..., alias="startTime", description="Start time in seconds")
    end_time: float = Field(..., alias="endTime", description="End time in seconds")
    start_beat_index: int = Field(..., alias="startBeatIndex", description="Beat index at start boundary")
    end_beat_index: int = Field(..., alias="endBeatIndex", description="Beat index at end boundary")
    start_frame_index: int = Field(..., alias="startFrameIndex", description="Frame index at start boundary (8 FPS)")
    end_frame_index: int = Field(..., alias="endFrameIndex", description="Frame index at end boundary (8 FPS)")
    start_alignment_error: float = Field(..., alias="startAlignmentError", description="Alignment error at start (seconds)")
    end_alignment_error: float = Field(..., alias="endAlignmentError", description="Alignment error at end (seconds)")
    duration_sec: float = Field(..., alias="durationSec", description="Clip duration in seconds")
    beats_in_clip: List[int] = Field(..., alias="beatsInClip", description="List of beat indices within this clip")

    model_config = {"populate_by_name": True}


class BeatAlignedBoundariesResponse(BaseModel):
    """Response for beat-aligned clip boundaries calculation."""

    boundaries: List[ClipBoundaryMetadata] = Field(..., description="List of clip boundaries")
    clip_count: int = Field(..., alias="clipCount", description="Number of clips")
    song_duration: float = Field(..., alias="songDuration", description="Total song duration in seconds")
    bpm: Optional[float] = Field(None, description="BPM used for calculation")
    fps: float = Field(default=24.0, description="Video FPS")
    total_beats: int = Field(..., alias="totalBeats", description="Total number of beats in song")
    max_alignment_error: float = Field(..., alias="maxAlignmentError", description="Worst alignment error across all boundaries (seconds)")
    avg_alignment_error: float = Field(..., alias="avgAlignmentError", description="Average alignment error (seconds)")
    validation_status: str = Field(..., alias="validationStatus", description="Validation status: 'valid' or 'warning'")

    model_config = {"populate_by_name": True}

