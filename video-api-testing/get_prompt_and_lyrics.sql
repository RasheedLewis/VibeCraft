-- Get the latest prompt and full lyrics from the database
-- Usage: psql postgresql://postgres:postgres@127.0.0.1:5433/ai_music_video -f get_prompt_and_lyrics.sql

WITH latest_prompt AS (
    SELECT 
        sv.song_id,
        sv.prompt,
        sv.section_id,
        sv.template,
        s.title as song_title
    FROM section_videos sv
    JOIN songs s ON sv.song_id = s.id
    WHERE sv.prompt IS NOT NULL AND sv.prompt != ''
    ORDER BY sv.created_at DESC
    LIMIT 1
),
song_analysis AS (
    SELECT 
        sa.analysis_json::jsonb as analysis
    FROM song_analyses sa
    JOIN latest_prompt lp ON sa.song_id = lp.song_id
)
SELECT 
    lp.prompt,
    lp.song_title,
    lp.section_id,
    lp.template,
    CASE 
        WHEN sa.analysis->>'lyricsAvailable' = 'true' 
        THEN (
            SELECT string_agg(lyric->>'text', E'\n' ORDER BY (lyric->>'startSec')::float)
            FROM jsonb_array_elements(sa.analysis->'sectionLyrics') as lyric
        )
        ELSE NULL
    END as full_lyrics
FROM latest_prompt lp
CROSS JOIN song_analysis sa;

