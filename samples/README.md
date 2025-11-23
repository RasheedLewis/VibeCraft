# Sample Audio Files

This directory contains sample audio files for testing and development.

## Directory Structure

```
samples/
  audio/
    electronic/    # EDM, techno, house tracks
    pop-rock/      # Pop and rock tracks
    hip-hop/       # Hip-hop and rap tracks
    ambient/       # Ambient and chill tracks
  metadata/        # JSON metadata files for each track
```

## Getting Sample Files

See `docs/SAMPLE_AUDIO_GUIDE.md` for recommended sources and download instructions.

## Recommended Sources

1. **Pixabay Music** - No attribution required, commercial use OK
2. **Free Music Archive** - Diverse selection, various licenses
3. **Incompetech** - CC BY license, attribution required

## Usage

- **Backend testing:** Use these files for audio analysis testing
- **Frontend testing:** Use for upload UI testing
- **Mock data:** Reference in mock section data files

## Attribution Tracking

When you download a song that requires attribution:
1. Add an entry to `ATTRIBUTION.md` with the filename and attribution text
2. (Optional) Create a metadata JSON file in `metadata/` with full details

**Quick reference:** Edit `samples/ATTRIBUTION.md` to track attribution for downloaded songs.

## License Notes

Each track should have its license documented in `metadata/` or `ATTRIBUTION.md`. Always verify license before using in demos or production.

