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

