# Differences Between analyze_local_song.py Files

## File Locations
1. **`video-api-testing/analyze_local_song.py`** - Original version in video-api-testing directory
2. **`backend/analyze_local_song.py`** - Updated version in backend directory

## Key Differences

### 1. **Path Resolution**
- **video-api-testing version**: 
  ```python
  backend_path = Path(__file__).parent.parent / "backend"
  sys.path.insert(0, str(backend_path))
  ```
  Assumes script is in `video-api-testing/` and needs to find `backend/` directory.

- **backend version**: 
  ```python
  sys.path.insert(0, str(Path(__file__).parent))
  ```
  Assumes script is already in `backend/` directory (simpler, but has duplicate lines).

### 2. **User ID**
- **video-api-testing version**: 
  ```python
  user_id="test-user"  # Hardcoded, may not exist in database
  ```

- **backend version**: 
  ```python
  from app.models import DEFAULT_USER_ID
  user_id=DEFAULT_USER_ID  # Uses the actual default user ID
  ```
  ✅ **Better**: Uses the proper default user that's created by `init_db()`.

### 3. **Tempo Handling**
- **video-api-testing version**: 
  ```python
  print(f"   BPM: {tempo:.1f}, Beats: {len(beat_times)}")
  bpm=float(tempo) if tempo else None,
  ```
  May fail if `tempo` is a numpy array.

- **backend version**: 
  ```python
  tempo_float = float(tempo) if hasattr(tempo, '__float__') else float(tempo[0]) if hasattr(tempo, '__len__') else 0.0
  tempo_value = float(tempo) if hasattr(tempo, '__float__') else float(tempo[0]) if hasattr(tempo, '__len__') and len(tempo) > 0 else None
  ```
  ✅ **Better**: Handles numpy arrays properly (though generates deprecation warnings).

### 4. **Final Message**
- **video-api-testing version**: 
  ```python
  print(f"   You can now query prompts with: sqlite3 ../backend/app.db < get_prompt_and_lyrics_sqlite.sql")
  ```
  ❌ **Wrong**: References SQLite.

- **backend version**: 
  ```python
  print(f"   You can now query prompts with:")
  print(f"   psql postgresql://postgres:postgres@127.0.0.1:5433/ai_music_video -f video-api-testing/get_prompt_and_lyrics_simple.sql")
  ```
  ✅ **Correct**: References PostgreSQL.

### 5. **Code Quality**
- **backend version** has duplicate `sys.path.insert` lines (lines 11 and 22), which is redundant but harmless.

## Recommendation

**Use `backend/analyze_local_song.py`** as it:
- Uses the correct `DEFAULT_USER_ID`
- Handles tempo/numpy arrays properly
- Has correct PostgreSQL references
- Is in the correct location (backend directory)

**Fix needed**: Remove duplicate `sys.path.insert` lines in backend version.

