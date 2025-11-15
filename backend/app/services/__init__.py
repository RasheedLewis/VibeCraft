from app.services.audio_preprocessing import AudioPreprocessingResult, preprocess_audio
from app.services.genre_mood_analysis import compute_genre,compute_mood_features, compute_mood_tags
from app.services.scene_planner import build_scene_spec
from app.services.lyric_extraction import (
    align_lyrics_to_sections,
    extract_and_align_lyrics,
    extract_lyrics_with_whisper,
    segment_lyrics_into_lines,
)
from app.services.mock_analysis import (
    get_mock_analysis_ambient,
    get_mock_analysis_by_section_id,
    get_mock_analysis_by_song_id,
    get_mock_analysis_country,
    get_mock_analysis_electronic,
    get_mock_analysis_hip_hop,
    get_mock_analysis_melancholic,
    get_mock_analysis_metal,
    get_mock_analysis_pop_rock,
    get_section_from_analysis,
    get_section_lyrics_from_analysis,
)

__all__ = [
    "align_lyrics_to_sections",
    "AudioPreprocessingResult",
    "build_scene_spec",
    "compute_genre",
    "compute_mood_features",
    "compute_mood_tags",
    "extract_and_align_lyrics",
    "extract_lyrics_with_whisper",
    "get_mock_analysis_ambient",
    "get_mock_analysis_by_section_id",
    "get_mock_analysis_by_song_id",
    "get_mock_analysis_country",
    "get_mock_analysis_electronic",
    "get_mock_analysis_hip_hop",
    "get_mock_analysis_melancholic",
    "get_mock_analysis_metal",
    "get_mock_analysis_pop_rock",
    "get_section_from_analysis",
    "get_section_lyrics_from_analysis",
    "preprocess_audio",
    "segment_lyrics_into_lines",
]
