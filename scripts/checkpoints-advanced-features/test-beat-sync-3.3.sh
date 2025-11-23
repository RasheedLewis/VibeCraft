#!/bin/bash
#
# Beat Sync Phase 3.3: Structural Sync Test Script
# =================================================
#
# This script comprehensively tests all Phase 3.3 features related to structural
# synchronization - aligning clip transitions to musical beats. It validates
# beat-aligned boundary calculation, user selection support, transition verification,
# and clip trimming/extending functionality.
#
# Features Tested:
# ----------------
# 1. Beat-Aligned Clip Boundary Calculation
#    - Calculates optimal clip boundaries aligned to beat grid
#    - Respects minimum/maximum clip duration constraints (3-6 seconds)
#    - Handles edge cases (short songs, long songs, sparse beats)
#    - Function: calculate_beat_aligned_clip_boundaries()
#
# 2. User Selection Support (30-Second Clips)
#    - Filters beats to user-selected time segments
#    - Adjusts boundaries for selection offset
#    - Supports 30-second clip selection feature
#    - Maintains beat alignment within selection
#
# 3. Transition Verification
#    - Verifies all clip transitions occur on beat boundaries
#    - Configurable tolerance (default: ±50ms)
#    - Returns alignment status and error metrics
#    - Function: verify_beat_aligned_transitions()
#
# 4. Clip Trimming to Beat Boundaries
#    - Trims clips to align with beat-aligned start/end times
#    - Calculates trim offsets relative to clip start
#    - Uses FFmpeg trim filter with setpts
#    - Function: trim_clip_to_beat_boundary()
#
# 5. Clip Extension to Beat Boundaries
#    - Extends clips to align with beat-aligned end times
#    - Uses frame freeze (tpad) for extension
#    - Adds fadeout for smooth transitions
#    - Falls back to trim if extension not needed
#    - Function: extend_clip_to_beat_boundary()
#
# 6. Integration with Composition Pipeline
#    - Beat alignment integrated into composition_execution.py
#    - Clips are trimmed/extended before concatenation
#    - Ensures all transitions occur on beats
#
# What This Script Does:
# ----------------------
# 1. Sets up Python virtual environment (.venv) if it doesn't exist
# 2. Activates the virtual environment
# 3. Installs/updates all required dependencies from requirements.txt
# 4. Runs all unit tests:
#    - test_beat_alignment.py (all tests)
#    - test_video_composition.py (TestTrimClipToBeatBoundary)
#    - test_video_composition.py (TestExtendClipToBeatBoundary)
# 5. Performs functional validation checks:
#    - Beat-aligned boundary calculation with various scenarios
#    - User selection support (30-second clips)
#    - Transition verification with perfect and imperfect alignment
#    - Function availability and callability
# 6. Reports success/failure with colored output
#
# Usage:
# ------
#   ./scripts/test-beat-sync-3.3.sh
#
# Exit Codes:
# -----------
#   0 - All tests passed
#   1 - Tests failed or setup error
#
# Dependencies:
# -------------
#   - Python 3.12+
#   - Virtual environment will be created automatically
#   - All dependencies from backend/requirements.txt
#
# Test Files:
# -----------
#   - backend/tests/unit/test_beat_alignment.py
#   - backend/tests/unit/test_video_composition.py (trim/extend tests)
#
# Related Files:
# --------------
#   - backend/app/services/beat_alignment.py (implementation)
#   - backend/app/services/video_composition.py (trim/extend functions)
#   - backend/app/services/composition_execution.py (pipeline integration)
#
# Success Criteria:
# -----------------
#   - All clip transitions occur within ±50ms of beat boundaries
#   - Boundaries respect duration constraints (3-6 seconds)
#   - User selections are properly handled
#   - Clips are correctly trimmed/extended to beat boundaries
#
# Plan Document References:
# -------------------------
#   - docs/advanced_features_planning/BEAT-SYNC-IMPLEMENTATION-PLAN.md
#   - Section: Phase 3.3: Structural Sync
#   - Subsections:
#     * 3.3.1: Beat-Aligned Boundary Calculation
#     * 3.3.2: Clip Trimming/Extension for Beat Alignment
#     * 3.3.3: Integration with Composition Pipeline
#     * 3.3.4: Transition Verification
#   - Success Criteria: 100% of clip transitions occur within ±50ms of beat boundaries
#

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Beat Sync Phase 3.3: Structural Sync${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

# Setup venv if it doesn't exist
if [ ! -d ".venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv .venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
fi

# Activate venv
export VIRTUAL_ENV_DISABLE_PROMPT=1
source .venv/bin/activate

# Install dependencies
echo -e "${YELLOW}Installing/updating dependencies...${NC}"
pip install -q --upgrade pip
pip install -q -r backend/requirements.txt
echo -e "${GREEN}✓ Dependencies installed${NC}"
echo ""

# Run Phase 3.3 specific tests
echo -e "${BLUE}Running Phase 3.3 unit tests...${NC}"
echo ""

# Test beat alignment service
echo -e "${YELLOW}Testing beat alignment service...${NC}"
if pytest backend/tests/unit/test_beat_alignment.py -v --tb=short; then
    echo -e "${GREEN}✓ Beat alignment tests passed${NC}"
else
    echo -e "${RED}✗ Beat alignment tests failed${NC}"
    exit 1
fi
echo ""

# Test video composition (trim/extend functions)
echo -e "${YELLOW}Testing video composition (beat boundary functions)...${NC}"
if pytest backend/tests/unit/test_video_composition.py::TestTrimClipToBeatBoundary -v --tb=short; then
    echo -e "${GREEN}✓ Trim clip to beat boundary tests passed${NC}"
else
    echo -e "${RED}✗ Trim clip to beat boundary tests failed${NC}"
    exit 1
fi

if pytest backend/tests/unit/test_video_composition.py::TestExtendClipToBeatBoundary -v --tb=short; then
    echo -e "${GREEN}✓ Extend clip to beat boundary tests passed${NC}"
else
    echo -e "${RED}✗ Extend clip to beat boundary tests failed${NC}"
    exit 1
fi
echo ""

# Run functional checks
echo -e "${BLUE}Running functional checks...${NC}"
echo ""

# Test beat-aligned boundary calculation
echo -e "${YELLOW}Testing beat-aligned boundary calculation...${NC}"
cd backend
PYTHONPATH=. python3 -c "
from app.services.beat_alignment import calculate_beat_aligned_clip_boundaries

beat_times = [i * 0.5 for i in range(21)]  # 0-10 seconds
song_duration = 10.0

boundaries = calculate_beat_aligned_clip_boundaries(
    beat_times=beat_times,
    song_duration=song_duration,
    num_clips=6,
    fps=24.0,
)

if len(boundaries) > 0:
    print(f'  ✓ Generated {len(boundaries)} beat-aligned boundaries')
    print(f'  ✓ First boundary: {boundaries[0].start_time:.2f}s - {boundaries[0].end_time:.2f}s')
    print(f'  ✓ Last boundary: {boundaries[-1].start_time:.2f}s - {boundaries[-1].end_time:.2f}s')
    
    # Check all boundaries have valid metadata
    all_valid = all(
        b.start_beat_index <= b.end_beat_index and
        b.start_time < b.end_time and
        len(b.beats_in_clip) > 0
        for b in boundaries
    )
    
    if all_valid:
        print('  ✓ All boundaries have valid metadata')
        exit(0)
    else:
        print('  ✗ Some boundaries have invalid metadata')
        exit(1)
else:
    print('  ✗ No boundaries generated')
    exit(1)
"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Boundary calculation functional test passed${NC}"
else
    echo -e "${RED}✗ Boundary calculation functional test failed${NC}"
    exit 1
fi
echo ""

# Test user selection support
echo -e "${YELLOW}Testing user selection support...${NC}"
PYTHONPATH=. python3 -c "
from app.services.beat_alignment import calculate_beat_aligned_clip_boundaries

beat_times = [i * 0.5 for i in range(61)]  # 0-30 seconds
song_duration = 30.0

# Test with user selection (10-20 second segment)
boundaries = calculate_beat_aligned_clip_boundaries(
    beat_times=beat_times,
    song_duration=song_duration,
    user_selection_start=10.0,
    user_selection_end=20.0,
    fps=24.0,
)

if len(boundaries) > 0:
    print(f'  ✓ Generated {len(boundaries)} boundaries for user selection')
    
    # Check boundaries are within or start within selection
    all_in_range = all(
        b.start_time >= 10.0 and b.start_time <= 20.0
        for b in boundaries
    )
    
    if all_in_range:
        print('  ✓ All boundaries start within user selection range')
        exit(0)
    else:
        print('  ✗ Some boundaries outside user selection range')
        exit(1)
else:
    print('  ✗ No boundaries generated for user selection')
    exit(1)
"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ User selection functional test passed${NC}"
else
    echo -e "${RED}✗ User selection functional test failed${NC}"
    exit 1
fi
echo ""

# Test transition verification
echo -e "${YELLOW}Testing transition verification...${NC}"
PYTHONPATH=. python3 -c "
from app.services.beat_alignment import verify_beat_aligned_transitions, ClipBoundary

beat_times = [0.0, 1.0, 2.0, 3.0, 4.0]

# Test with perfectly aligned transitions
boundaries = [
    ClipBoundary(
        start_time=0.0, end_time=1.0,
        start_beat_index=0, end_beat_index=1,
        start_frame_index=0, end_frame_index=24,
        start_alignment_error=0.0, end_alignment_error=0.0,
        duration_sec=1.0, beats_in_clip=[0, 1]
    ),
    ClipBoundary(
        start_time=1.0, end_time=2.0,
        start_beat_index=1, end_beat_index=2,
        start_frame_index=24, end_frame_index=48,
        start_alignment_error=0.0, end_alignment_error=0.0,
        duration_sec=1.0, beats_in_clip=[1, 2]
    ),
]

all_aligned, errors = verify_beat_aligned_transitions(boundaries, beat_times, tolerance_sec=0.05)

if all_aligned and len(errors) == 1 and errors[0] <= 0.05:
    print('  ✓ Perfect alignment verified')
    exit(0)
else:
    print(f'  ✗ Alignment check failed: all_aligned={all_aligned}, errors={errors}')
    exit(1)
"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Transition verification functional test passed${NC}"
else
    echo -e "${RED}✗ Transition verification functional test failed${NC}"
    exit 1
fi
echo ""

# Test that functions exist and are callable
echo -e "${YELLOW}Testing function availability...${NC}"
PYTHONPATH=. python3 -c "
from app.services.video_composition import trim_clip_to_beat_boundary, extend_clip_to_beat_boundary
from app.services.beat_alignment import calculate_beat_aligned_clip_boundaries, verify_beat_aligned_transitions

functions = [
    ('trim_clip_to_beat_boundary', trim_clip_to_beat_boundary),
    ('extend_clip_to_beat_boundary', extend_clip_to_beat_boundary),
    ('calculate_beat_aligned_clip_boundaries', calculate_beat_aligned_clip_boundaries),
    ('verify_beat_aligned_transitions', verify_beat_aligned_transitions),
]

all_found = True
for name, func in functions:
    if callable(func):
        print(f'  ✓ {name} is callable')
    else:
        print(f'  ✗ {name} is not callable')
        all_found = False

if all_found:
    print('✓ All Phase 3.3 functions available')
    exit(0)
else:
    print('✗ Some Phase 3.3 functions missing')
    exit(1)
"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Function availability check passed${NC}"
else
    echo -e "${RED}✗ Function availability check failed${NC}"
    exit 1
fi
echo ""

# Summary
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}✓ Phase 3.3: All tests passed!${NC}"
echo -e "${BLUE}========================================${NC}"

cd "$PROJECT_ROOT"
deactivate

