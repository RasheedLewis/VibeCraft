"""Mock SongAnalysis data for PR-08 development.

Use this for testing scene planner until Person A completes PR-04.
One SongAnalysis per song, containing multiple sections (typically 5-7 per song).
"""

from app.schemas.analysis import (
    MoodVector,
    SectionLyrics,
    SongAnalysis,
    SongSection,
)


def get_mock_analysis_electronic() -> SongAnalysis:
    """Mock analysis for an Electronic/EDM track (~3:30)."""
    return SongAnalysis(
        duration_sec=250.0,
        bpm=128.0,
        sections=[
            SongSection(
                id="section-1",
                type="intro",
                startSec=0.0,
                endSec=16.0,
                confidence=0.95,
            ),
            SongSection(
                id="section-2",
                type="verse",
                startSec=16.0,
                endSec=48.0,
                confidence=0.92,
                repetitionGroup="verse-1",
            ),
            SongSection(
                id="section-3",
                type="pre_chorus",
                startSec=48.0,
                endSec=64.0,
                confidence=0.88,
            ),
            SongSection(
                id="section-4",
                type="chorus",
                startSec=64.0,
                endSec=96.0,
                confidence=0.98,
                repetitionGroup="chorus-1",
            ),
            SongSection(
                id="section-5",
                type="verse",
                startSec=96.0,
                endSec=128.0,
                confidence=0.91,
                repetitionGroup="verse-2",
            ),
            SongSection(
                id="section-6",
                type="pre_chorus",
                startSec=128.0,
                endSec=144.0,
                confidence=0.87,
            ),
            SongSection(
                id="section-7",
                type="chorus",
                startSec=144.0,
                endSec=176.0,
                confidence=0.97,
                repetitionGroup="chorus-2",
            ),
            SongSection(
                id="section-8",
                type="bridge",
                startSec=176.0,
                endSec=200.0,
                confidence=0.85,
            ),
            SongSection(
                id="section-9",
                type="chorus",
                startSec=200.0,
                endSec=232.0,
                confidence=0.96,
                repetitionGroup="chorus-3",
            ),
            SongSection(
                id="section-10",
                type="outro",
                startSec=232.0,
                endSec=250.0,
                confidence=0.93,
            ),
        ],
        mood_primary="energetic",
        mood_tags=["energetic", "upbeat", "danceable", "happy"],
        mood_vector=MoodVector(
            energy=0.85,
            valence=0.75,
            danceability=0.90,
            tension=0.45,
        ),
        primary_genre="Electronic",
        sub_genres=["Synth-Pop", "EDM"],
        lyrics_available=True,
        section_lyrics=[
            SectionLyrics(
                sectionId="section-2",
                startSec=16.0,
                endSec=48.0,
                text="Moving through the night, feeling the beat inside...",
            ),
            SectionLyrics(
                sectionId="section-4",
                startSec=64.0,
                endSec=96.0,
                text="Dance with me tonight, we're free and alive...",
            ),
            SectionLyrics(
                sectionId="section-7",
                startSec=144.0,
                endSec=176.0,
                text="Dance with me tonight, we're free and alive...",
            ),
        ],
    )


def get_mock_analysis_pop_rock() -> SongAnalysis:
    """Mock analysis for a Pop/Rock track (~4:00)."""
    return SongAnalysis(
        duration_sec=240.0,
        bpm=115.0,
        sections=[
            SongSection(
                id="section-1",
                type="intro",
                startSec=0.0,
                endSec=20.0,
                confidence=0.94,
            ),
            SongSection(
                id="section-2",
                type="verse",
                startSec=20.0,
                endSec=52.0,
                confidence=0.93,
                repetitionGroup="verse-1",
            ),
            SongSection(
                id="section-3",
                type="chorus",
                startSec=52.0,
                endSec=84.0,
                confidence=0.97,
                repetitionGroup="chorus-1",
            ),
            SongSection(
                id="section-4",
                type="verse",
                startSec=84.0,
                endSec=116.0,
                confidence=0.92,
                repetitionGroup="verse-2",
            ),
            SongSection(
                id="section-5",
                type="chorus",
                startSec=116.0,
                endSec=148.0,
                confidence=0.98,
                repetitionGroup="chorus-2",
            ),
            SongSection(
                id="section-6",
                type="solo",
                startSec=148.0,
                endSec=180.0,
                confidence=0.89,
            ),
            SongSection(
                id="section-7",
                type="chorus",
                startSec=180.0,
                endSec=212.0,
                confidence=0.96,
                repetitionGroup="chorus-3",
            ),
            SongSection(
                id="section-8",
                type="outro",
                startSec=212.0,
                endSec=240.0,
                confidence=0.91,
            ),
        ],
        mood_primary="energetic",
        mood_tags=["energetic", "upbeat", "intense"],
        mood_vector=MoodVector(
            energy=0.80,
            valence=0.65,
            danceability=0.70,
            tension=0.70,
        ),
        primary_genre="Rock",
        sub_genres=["Alternative Rock", "Pop Rock"],
        lyrics_available=True,
        section_lyrics=[
            SectionLyrics(
                sectionId="section-2",
                startSec=20.0,
                endSec=52.0,
                text="Walking down the street, feeling the heat...",
            ),
            SectionLyrics(
                sectionId="section-3",
                startSec=52.0,
                endSec=84.0,
                text="We're breaking free, can't you see...",
            ),
        ],
    )


def get_mock_analysis_country() -> SongAnalysis:
    """Mock analysis for a Country track (~3:30)."""
    return SongAnalysis(
        duration_sec=210.0,
        bpm=95.0,
        sections=[
            SongSection(
                id="section-1",
                type="intro",
                startSec=0.0,
                endSec=15.0,
                confidence=0.92,
            ),
            SongSection(
                id="section-2",
                type="verse",
                startSec=15.0,
                endSec=45.0,
                confidence=0.94,
                repetitionGroup="verse-1",
            ),
            SongSection(
                id="section-3",
                type="chorus",
                startSec=45.0,
                endSec=75.0,
                confidence=0.96,
                repetitionGroup="chorus-1",
            ),
            SongSection(
                id="section-4",
                type="verse",
                startSec=75.0,
                endSec=105.0,
                confidence=0.93,
                repetitionGroup="verse-2",
            ),
            SongSection(
                id="section-5",
                type="chorus",
                startSec=105.0,
                endSec=135.0,
                confidence=0.97,
                repetitionGroup="chorus-2",
            ),
            SongSection(
                id="section-6",
                type="bridge",
                startSec=135.0,
                endSec=165.0,
                confidence=0.88,
            ),
            SongSection(
                id="section-7",
                type="chorus",
                startSec=165.0,
                endSec=195.0,
                confidence=0.95,
                repetitionGroup="chorus-3",
            ),
            SongSection(
                id="section-8",
                type="outro",
                startSec=195.0,
                endSec=210.0,
                confidence=0.90,
            ),
        ],
        mood_primary="calm",
        mood_tags=["calm", "relaxed", "melancholic"],
        mood_vector=MoodVector(
            energy=0.55,
            valence=0.50,
            danceability=0.50,
            tension=0.40,
        ),
        primary_genre="Country",
        sub_genres=["Country Folk"],
        lyrics_available=True,
        section_lyrics=[
            SectionLyrics(
                sectionId="section-2",
                startSec=15.0,
                endSec=45.0,
                text="Do you punish yourself like me? Though you know it's not what you need...",
            ),
            SectionLyrics(
                sectionId="section-3",
                startSec=45.0,
                endSec=75.0,
                text="I wonder if you feel like I do, walking down this lonely road...",
            ),
        ],
    )


def get_mock_analysis_by_song_id(song_id: str) -> SongAnalysis:
    """Get mock analysis based on song ID pattern.
    
    Args:
        song_id: Song identifier (can include genre keywords)
        
    Returns:
        Mock SongAnalysis object
    """
    song_id_lower = song_id.lower()
    
    if "electronic" in song_id_lower or "edm" in song_id_lower:
        return get_mock_analysis_electronic()
    elif "pop" in song_id_lower or "rock" in song_id_lower:
        return get_mock_analysis_pop_rock()
    elif "country" in song_id_lower:
        return get_mock_analysis_country()
    elif "hip" in song_id_lower or "hop" in song_id_lower or "rap" in song_id_lower:
        return get_mock_analysis_hip_hop()
    elif "ambient" in song_id_lower:
        return get_mock_analysis_ambient()
    elif "metal" in song_id_lower:
        return get_mock_analysis_metal()
    elif "melancholic" in song_id_lower or "sad" in song_id_lower:
        return get_mock_analysis_melancholic()
    else:
        # Default to electronic
        return get_mock_analysis_electronic()


def get_mock_analysis_hip_hop() -> SongAnalysis:
    """Mock analysis for a Hip-Hop track (~3:15)."""
    return SongAnalysis(
        duration_sec=195.0,
        bpm=95.0,
        sections=[
            SongSection(
                id="section-1",
                type="intro",
                startSec=0.0,
                endSec=12.0,
                confidence=0.96,
            ),
            SongSection(
                id="section-2",
                type="verse",
                startSec=12.0,
                endSec=48.0,
                confidence=0.94,
                repetitionGroup="verse-1",
            ),
            SongSection(
                id="section-3",
                type="chorus",
                startSec=48.0,
                endSec=72.0,
                confidence=0.99,
                repetitionGroup="hook-1",
            ),
            SongSection(
                id="section-4",
                type="verse",
                startSec=72.0,
                endSec=108.0,
                confidence=0.93,
                repetitionGroup="verse-2",
            ),
            SongSection(
                id="section-5",
                type="chorus",
                startSec=108.0,
                endSec=132.0,
                confidence=0.98,
                repetitionGroup="hook-2",
            ),
            SongSection(
                id="section-6",
                type="bridge",
                startSec=132.0,
                endSec=156.0,
                confidence=0.87,
            ),
            SongSection(
                id="section-7",
                type="chorus",
                startSec=156.0,
                endSec=180.0,
                confidence=0.97,
                repetitionGroup="hook-3",
            ),
            SongSection(
                id="section-8",
                type="outro",
                startSec=180.0,
                endSec=195.0,
                confidence=0.92,
            ),
        ],
        mood_primary="intense",
        mood_tags=["intense", "energetic", "danceable"],
        mood_vector=MoodVector(
            energy=0.75,
            valence=0.60,
            danceability=0.85,
            tension=0.75,
        ),
        primary_genre="Hip-Hop",
        sub_genres=["Trap", "Rap"],
        lyrics_available=True,
        section_lyrics=[
            SectionLyrics(
                sectionId="section-2",
                startSec=12.0,
                endSec=48.0,
                text="Living life on the edge, making moves, breaking rules...",
            ),
            SectionLyrics(
                sectionId="section-3",
                startSec=48.0,
                endSec=72.0,
                text="We run this city, can't stop us now...",
            ),
        ],
    )


def get_mock_analysis_ambient() -> SongAnalysis:
    """Mock analysis for an Ambient track (~4:00) - minimal sections, no lyrics."""
    return SongAnalysis(
        duration_sec=240.0,
        bpm=70.0,
        sections=[
            SongSection(
                id="section-1",
                type="intro",
                startSec=0.0,
                endSec=60.0,
                confidence=0.90,
            ),
            SongSection(
                id="section-2",
                type="other",
                startSec=60.0,
                endSec=180.0,
                confidence=0.85,
            ),
            SongSection(
                id="section-3",
                type="outro",
                startSec=180.0,
                endSec=240.0,
                confidence=0.88,
            ),
        ],
        mood_primary="calm",
        mood_tags=["calm", "relaxed", "ambient"],
        mood_vector=MoodVector(
            energy=0.25,
            valence=0.45,
            danceability=0.15,
            tension=0.20,
        ),
        primary_genre="Ambient",
        sub_genres=["Ambient Electronic"],
        lyrics_available=False,
        section_lyrics=None,
    )


def get_mock_analysis_metal() -> SongAnalysis:
    """Mock analysis for a Metal track (~3:45) - high energy, high tension."""
    return SongAnalysis(
        duration_sec=225.0,
        bpm=160.0,
        sections=[
            SongSection(
                id="section-1",
                type="intro",
                startSec=0.0,
                endSec=15.0,
                confidence=0.95,
            ),
            SongSection(
                id="section-2",
                type="verse",
                startSec=15.0,
                endSec=45.0,
                confidence=0.93,
                repetitionGroup="verse-1",
            ),
            SongSection(
                id="section-3",
                type="chorus",
                startSec=45.0,
                endSec=75.0,
                confidence=0.97,
                repetitionGroup="chorus-1",
            ),
            SongSection(
                id="section-4",
                type="verse",
                startSec=75.0,
                endSec=105.0,
                confidence=0.92,
                repetitionGroup="verse-2",
            ),
            SongSection(
                id="section-5",
                type="chorus",
                startSec=105.0,
                endSec=135.0,
                confidence=0.98,
                repetitionGroup="chorus-2",
            ),
            SongSection(
                id="section-6",
                type="solo",
                startSec=135.0,
                endSec=180.0,
                confidence=0.90,
            ),
            SongSection(
                id="section-7",
                type="chorus",
                startSec=180.0,
                endSec=210.0,
                confidence=0.96,
                repetitionGroup="chorus-3",
            ),
            SongSection(
                id="section-8",
                type="outro",
                startSec=210.0,
                endSec=225.0,
                confidence=0.94,
            ),
        ],
        mood_primary="intense",
        mood_tags=["intense", "energetic", "aggressive"],
        mood_vector=MoodVector(
            energy=0.95,
            valence=0.35,
            danceability=0.60,
            tension=0.90,
        ),
        primary_genre="Metal",
        sub_genres=["Heavy Metal", "Thrash"],
        lyrics_available=True,
        section_lyrics=[
            SectionLyrics(
                sectionId="section-2",
                startSec=15.0,
                endSec=45.0,
                text="Raging through the fire, nothing can stop us now...",
            ),
            SectionLyrics(
                sectionId="section-3",
                startSec=45.0,
                endSec=75.0,
                text="Breaking chains, we rise again...",
            ),
        ],
    )


def get_mock_analysis_melancholic() -> SongAnalysis:
    """Mock analysis for a melancholic/sad track - low valence, low energy."""
    return SongAnalysis(
        duration_sec=200.0,
        bpm=85.0,
        sections=[
            SongSection(
                id="section-1",
                type="intro",
                startSec=0.0,
                endSec=20.0,
                confidence=0.91,
            ),
            SongSection(
                id="section-2",
                type="verse",
                startSec=20.0,
                endSec=50.0,
                confidence=0.94,
                repetitionGroup="verse-1",
            ),
            SongSection(
                id="section-3",
                type="chorus",
                startSec=50.0,
                endSec=80.0,
                confidence=0.96,
                repetitionGroup="chorus-1",
            ),
            SongSection(
                id="section-4",
                type="verse",
                startSec=80.0,
                endSec=110.0,
                confidence=0.93,
                repetitionGroup="verse-2",
            ),
            SongSection(
                id="section-5",
                type="chorus",
                startSec=110.0,
                endSec=140.0,
                confidence=0.97,
                repetitionGroup="chorus-2",
            ),
            SongSection(
                id="section-6",
                type="bridge",
                startSec=140.0,
                endSec=170.0,
                confidence=0.89,
            ),
            SongSection(
                id="section-7",
                type="chorus",
                startSec=170.0,
                endSec=200.0,
                confidence=0.95,
                repetitionGroup="chorus-3",
            ),
        ],
        mood_primary="melancholic",
        mood_tags=["melancholic", "sad", "calm"],
        mood_vector=MoodVector(
            energy=0.40,
            valence=0.20,
            danceability=0.30,
            tension=0.35,
        ),
        primary_genre="Other",
        sub_genres=["Indie", "Folk"],
        lyrics_available=True,
        section_lyrics=[
            SectionLyrics(
                sectionId="section-2",
                startSec=20.0,
                endSec=50.0,
                text="All the colors fade away, nothing left to say...",
            ),
            SectionLyrics(
                sectionId="section-3",
                startSec=50.0,
                endSec=80.0,
                text="I'm lost in the silence, can't find my way home...",
            ),
        ],
    )


def get_mock_analysis_by_section_id(section_id: str) -> SongAnalysis:
    """Get mock analysis containing the specified section.
    
    Args:
        section_id: Section identifier (e.g., "section-4")
        
    Returns:
        Mock SongAnalysis object containing that section
    """
    # For now, return electronic (has sections 1-10)
    # In real implementation, would look up which song contains this section
    return get_mock_analysis_electronic()


def get_section_from_analysis(analysis: SongAnalysis, section_id: str) -> SongSection | None:
    """Helper to extract a specific section from SongAnalysis.
    
    Args:
        analysis: SongAnalysis object
        section_id: Section identifier to find
        
    Returns:
        SongSection if found, None otherwise
    """
    for section in analysis.sections:
        if section.id == section_id:
            return section
    return None


def get_section_lyrics_from_analysis(
    analysis: SongAnalysis, section_id: str
) -> SectionLyrics | None:
    """Helper to extract lyrics for a specific section.
    
    Args:
        analysis: SongAnalysis object
        section_id: Section identifier to find lyrics for
        
    Returns:
        SectionLyrics if found, None otherwise
    """
    if not analysis.section_lyrics:
        return None
    
    for lyrics in analysis.section_lyrics:
        if lyrics.section_id == section_id:
            return lyrics
    return None

