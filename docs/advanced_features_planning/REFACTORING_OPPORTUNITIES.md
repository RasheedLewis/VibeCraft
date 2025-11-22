# Refactoring Opportunities

Based on recent changes in this branch, here are the most impactful refactoring opportunities:

---

## 🔴 High Priority: Beat Filter Effect Logic Duplication

**Issue:** Beat filter effect type logic is duplicated across multiple locations with slight variations.

**Current State:**
- `video_composition.py` lines 475-521: Main effect application logic (5 effect types)
- `video_composition.py` lines 536-552: Chunking logic (duplicates flash and glitch only)
- `beat_filters.py`: Similar logic but different implementation approach

**Problems:**
1. **Code duplication:** Same if/elif chains in multiple places
2. **Maintenance burden:** Adding new effects requires changes in 2-3 places
3. **Inconsistency risk:** Test mode calculations differ slightly between locations
4. **Hard to test:** Logic scattered makes unit testing difficult

**Refactoring Approach:**

```python
# New: backend/app/services/beat_filter_applicator.py
class BeatFilterApplicator:
    """Centralized beat filter application logic."""
    
    def apply_filter(
        self,
        video_stream,
        beat_condition: str,
        filter_type: str,
        effect_config: BeatEffectConfig,
        test_mode: bool = False,
    ) -> VideoStream:
        """Apply a single beat filter to video stream."""
        # Single source of truth for all effect types
        # Returns configured ffmpeg filter
        
    def get_test_mode_multipliers(self, filter_type: str) -> dict:
        """Get test mode intensity multipliers for each effect type."""
        
    def should_chunk(self, filter_type: str, beat_count: int) -> bool:
        """Determine if effect needs chunking."""
```

**Benefits:**
- Single source of truth for effect logic
- Easy to add new effects (one place)
- Consistent test mode behavior
- Testable in isolation
- Reduces `video_composition.py` from ~150 lines to ~50 lines for beat filters

**Estimated Impact:** High - affects core video processing, reduces maintenance burden significantly

---

## 🟡 Medium Priority: Song Ownership Verification

**Issue:** Pattern of checking song ownership is repeated in multiple endpoints.

**Current State:**
- `routes_songs.py:get_song()` - checks `song.user_id != current_user.id`
- Likely needed in other endpoints that modify songs

**Problems:**
1. **Repeated code:** Same ownership check pattern
2. **Inconsistent error messages:** Could vary between endpoints
3. **Easy to forget:** New endpoints might miss ownership checks

**Refactoring Approach:**

```python
# New: backend/app/api/v1/utils.py
def verify_song_ownership(song: Song, current_user: User) -> None:
    """Verify song belongs to current user, raise 403 if not."""
    if song.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Song does not belong to you",
        )
```

**Usage:**
```python
def get_song(song_id: UUID, current_user: User = Depends(get_current_user), ...):
    song = get_song_or_404(song_id, db)
    verify_song_ownership(song, current_user)  # One line
    return song
```

**Benefits:**
- Consistent ownership checks
- Clear error messages
- DRY principle
- Easy to add to new endpoints

**Estimated Impact:** Medium - improves code quality, prevents security bugs

---

## 🟡 Medium Priority: Test Mode Configuration Extraction

**Issue:** Test mode logic and intensity multipliers are hardcoded in multiple places.

**Current State:**
- Test mode check: `os.getenv("BEAT_EFFECT_TEST_MODE", "false").lower() == "true"`
- Intensity multipliers scattered: `3 if test_mode else 1`, `0.8 if test_mode else 0.3`, etc.
- Tolerance calculations duplicated

**Problems:**
1. **Magic numbers:** Test mode multipliers hardcoded
2. **Inconsistent:** Different multipliers in different places
3. **Hard to configure:** Can't easily adjust test mode behavior

**Refactoring Approach:**

```python
# New: backend/app/core/config.py
class BeatEffectTestConfig:
    """Test mode configuration for beat effects."""
    enabled: bool = Field(default=False, alias="BEAT_EFFECT_TEST_MODE")
    tolerance_multiplier: float = 3.0  # 150ms vs 50ms
    flash_intensity_multiplier: float = 3.0
    glitch_intensity_test: float = 0.8
    glitch_intensity_normal: float = 0.3
    # ... etc for all effects
```

**Benefits:**
- Centralized test mode config
- Easy to adjust test behavior
- Consistent multipliers
- Can be toggled per-effect type

**Estimated Impact:** Medium - improves testability and configuration management

---

## 🟢 Low Priority: Beat Condition Building Logic

**Issue:** Logic for building beat conditions is duplicated between main path and chunking path.

**Current State:**
- Lines 464-468: Build beat conditions for main path
- Lines 531-534: Build beat conditions for chunking path (same logic)

**Refactoring Approach:**

```python
# Extract to helper function
def build_beat_conditions(
    beat_times: list[float],
    tolerance_sec: float,
    song_duration_sec: float,
) -> list[str]:
    """Build list of beat condition expressions."""
    beat_conditions = []
    for beat_time in beat_times:
        start_time = max(0, beat_time - tolerance_sec)
        end_time = min(beat_time + tolerance_sec, song_duration_sec)
        beat_conditions.append(f"between(t,{start_time},{end_time})")
    return beat_conditions
```

**Benefits:**
- DRY principle
- Easier to test
- Consistent logic

**Estimated Impact:** Low - small code quality improvement

---

## 🟢 Low Priority: Auth Response Model Consolidation

**Issue:** `AuthResponse` and `UserInfoResponse` have overlapping fields.

**Current State:**
- `AuthResponse`: access_token, user_id, email, display_name
- `UserInfoResponse`: user_id, email, display_name (no token)

**Refactoring Approach:**

```python
# Use composition instead of duplication
class UserInfo(BaseModel):
    """Base user information."""
    user_id: str
    email: str
    display_name: Optional[str] = None

class AuthResponse(UserInfo):
    """Authentication response includes token."""
    access_token: str

class UserInfoResponse(UserInfo):
    """User info without token."""
    pass
```

**Benefits:**
- Single source of truth for user fields
- Type safety
- Easier to extend

**Estimated Impact:** Low - minor code quality improvement

---

## 🟡 Medium Priority: Rate Limiting Identifier Extraction

**Issue:** `get_client_identifier` logic could be improved and made more testable.

**Current State:**
- Token extraction logic mixed with identifier generation
- Hard to test different scenarios
- JWT decoding not actually implemented (uses token prefix)

**Refactoring Approach:**

```python
# Improve rate limiting identifier extraction
def extract_user_id_from_token(token: str) -> Optional[str]:
    """Extract user ID from JWT token."""
    # Actually decode JWT instead of using prefix
    user_id = decode_access_token(token)
    return user_id

def get_client_identifier(request: Request) -> str:
    """Get identifier for rate limiting."""
    # Try user ID first (more accurate)
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header.replace("Bearer ", "")
        user_id = extract_user_id_from_token(token)
        if user_id:
            return f"user:{user_id}"
    
    # Fall back to IP
    client_ip = request.client.host if request.client else "unknown"
    return f"ip:{client_ip}"
```

**Benefits:**
- More accurate rate limiting (per-user vs per-IP)
- Testable components
- Better separation of concerns

**Estimated Impact:** Medium - improves rate limiting accuracy

---

## 🟢 Low Priority: Cost Tracking Service Consolidation

**Issue:** Cost calculation and storage could be more cohesive.

**Current State:**
- `cost_tracking.py` has both estimation and storage
- Storage logic could be extracted to repository pattern

**Refactoring Approach:**

```python
# Consider repository pattern for cost updates
class CostRepository:
    """Repository for cost-related operations."""
    
    @staticmethod
    def add_cost_to_song(song_id: UUID, cost: float) -> None:
        """Add cost to song's total."""
        # Centralized cost update logic
```

**Benefits:**
- Better separation of concerns
- Easier to test
- Consistent with other repository patterns

**Estimated Impact:** Low - minor architectural improvement

---

## 📊 Summary

**High Priority (Do First):**
1. Beat Filter Effect Logic Duplication - **Biggest impact, reduces maintenance burden**

**Medium Priority (Do Soon):**
2. Song Ownership Verification - **Security and consistency**
3. Test Mode Configuration - **Better testability**
4. Rate Limiting Identifier - **More accurate rate limiting**

**Low Priority (Nice to Have):**
5. Beat Condition Building - **Small code quality win**
6. Auth Response Models - **Minor type safety improvement**
7. Cost Tracking Consolidation - **Architectural consistency**

---

## Implementation Order

1. **Start with Beat Filter refactoring** - Highest impact, affects core functionality
2. **Add ownership verification** - Quick win, improves security
3. **Extract test mode config** - Makes testing easier
4. **Improve rate limiting** - Better user experience
5. **Polish with low-priority items** - As time permits

---

## Notes

- All refactorings should be done with tests in place
- Consider feature flags for risky refactorings
- Measure performance impact for beat filter refactoring (should be minimal)
- Keep backward compatibility during refactoring

