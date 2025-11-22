#!/bin/bash
#
# Beat Sync Phase 3.2: Audio-Reactive FFmpeg Filters Test Script
# =============================================================
#
# This script comprehensively tests all Phase 3.2 features related to audio-reactive
# FFmpeg filters for visual beat synchronization. It validates filter generation,
# effect parameter customization, frame-accurate timing, and all filter types.
#
# Features Tested:
# ----------------
# 1. Frame-Accurate Beat Time Conversion
#    - Converts beat timestamps to precise frame indices
#    - Handles video start time offsets
#    - Filters beats that occur before video start
#    - Function: convert_beat_times_to_frames()
#
# 2. Beat Filter Expression Generation
#    - Generates FFmpeg filter expressions for beat-reactive effects
#    - Supports multiple filter types: flash, color_burst, zoom_pulse, 
#      brightness_pulse, glitch
#    - Customizable effect parameters (intensity, color, saturation, etc.)
#    - Function: generate_beat_filter_expression()
#
# 3. Beat Filter Complex Generation
#    - Generates filter_complex expressions for advanced effects
#    - Creates time-based filter selections for each beat
#    - Supports combining multiple filters
#    - Function: generate_beat_filter_complex()
#
# 4. Glitch Effect Filter
#    - RGB channel shift effect for digital glitch aesthetic
#    - Customizable intensity (0.0-1.0)
#    - Pixel-level channel displacement
#
# 5. Effect Parameter Customization
#    - Flash: intensity, color
#    - Color Burst: saturation, brightness, hue
#    - Zoom Pulse: zoom amount, duration
#    - Glitch: intensity
#    - Brightness Pulse: brightness amount
#
# 6. Configuration System
#    - BeatEffectConfig in config.py
#    - Environment variable support for all effect parameters
#    - Default values for all effects
#
# What This Script Does:
# ----------------------
# 1. Sets up Python virtual environment (.venv) if it doesn't exist
# 2. Activates the virtual environment
# 3. Installs/updates all required dependencies from requirements.txt
# 4. Runs all unit tests in test_beat_filters.py
# 5. Performs functional validation checks:
#    - Frame-accurate beat time to frame conversion
#    - Filter generation with custom effect parameters
#    - Glitch effect registration and generation
#    - Filter complex generation for multiple beats
# 6. Reports success/failure with colored output
#
# Usage:
# ------
#   ./scripts/test-beat-sync-3.2.sh
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
#   - backend/tests/unit/test_beat_filters.py
#
# Related Files:
# --------------
#   - backend/app/services/beat_filters.py (implementation)
#   - backend/app/core/config.py (BeatEffectConfig)
#   - backend/app/services/video_composition.py (integration)
#   - backend/app/services/composition_execution.py (integration)
#
# Plan Document References:
# -------------------------
#   - docs/advanced_features_planning/BEAT-SYNC-IMPLEMENTATION-PLAN.md
#   - Section: Phase 3.2: Audio-Reactive FFmpeg Filters
#   - Subsections:
#     * 3.2.1: Beat Effect Service
#     * 3.2.2: Integration with Video Composition
#     * 3.2.3: Effect Configuration
#     * 3.2.4: Frame-Accurate Timing
#   - Success Criteria: Visual effects trigger within ±20ms of beat timestamps (frame-accurate)
#

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Beat Sync Phase 3.2: Audio-Reactive Filters${NC}"
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

# Run Phase 3.2 specific tests
echo -e "${BLUE}Running Phase 3.2 unit tests...${NC}"
echo ""

# Test beat filters service
echo -e "${YELLOW}Testing beat filters service...${NC}"
if pytest backend/tests/unit/test_beat_filters.py -v --tb=short; then
    echo -e "${GREEN}✓ Beat filters tests passed${NC}"
else
    echo -e "${RED}✗ Beat filters tests failed${NC}"
    exit 1
fi
echo ""

# Run functional checks
echo -e "${BLUE}Running functional checks...${NC}"
echo ""

# Test frame conversion
echo -e "${YELLOW}Testing frame-accurate beat time conversion...${NC}"
cd backend
PYTHONPATH=. python3 -c "
from app.services.beat_filters import convert_beat_times_to_frames

beat_times = [0.0, 0.5, 1.0, 1.5, 2.0]
frames = convert_beat_times_to_frames(beat_times, video_fps=24.0)

expected_frames = [0, 12, 24, 36, 48]
all_passed = True

for i, (beat_time, frame) in enumerate(zip(beat_times, frames)):
    expected = expected_frames[i]
    if frame == expected:
        print(f'  ✓ Beat {beat_time}s -> Frame {frame} (expected {expected})')
    else:
        print(f'  ✗ Beat {beat_time}s -> Frame {frame} (expected {expected})')
        all_passed = False

if all_passed:
    print('✓ All frame conversion tests passed')
    exit(0)
else:
    print('✗ Some frame conversion tests failed')
    exit(1)
"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Frame conversion functional test passed${NC}"
else
    echo -e "${RED}✗ Frame conversion functional test failed${NC}"
    exit 1
fi
echo ""

# Test filter generation with effect params
echo -e "${YELLOW}Testing filter generation with effect parameters...${NC}"
PYTHONPATH=. python3 -c "
from app.services.beat_filters import generate_beat_filter_expression

beat_times = [1.0, 2.0, 3.0]
test_cases = [
    ('flash', {'intensity': 100}, True),
    ('color_burst', {'saturation': 2.0, 'brightness': 0.2}, True),
    ('glitch', {'intensity': 0.5}, True),
    ('zoom_pulse', {'zoom': 1.1}, True),
]

all_passed = True
for filter_type, params, should_work in test_cases:
    try:
        result = generate_beat_filter_expression(beat_times, filter_type=filter_type, effect_params=params)
        if result and len(result) > 0:
            print(f'  ✓ {filter_type}: Filter generated with custom params')
        else:
            print(f'  ✗ {filter_type}: Empty filter generated')
            all_passed = False
    except Exception as e:
        print(f'  ✗ {filter_type}: Error - {e}')
        all_passed = False

if all_passed:
    print('✓ All effect parameter tests passed')
    exit(0)
else:
    print('✗ Some effect parameter tests failed')
    exit(1)
"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Effect parameters functional test passed${NC}"
else
    echo -e "${RED}✗ Effect parameters functional test failed${NC}"
    exit 1
fi
echo ""

# Test glitch effect
echo -e "${YELLOW}Testing glitch effect filter...${NC}"
PYTHONPATH=. python3 -c "
from app.services.beat_filters import generate_beat_filter_expression, FILTER_TYPES

# Check glitch is in FILTER_TYPES
if 'glitch' in FILTER_TYPES:
    print('  ✓ Glitch effect registered in FILTER_TYPES')
else:
    print('  ✗ Glitch effect not found in FILTER_TYPES')
    exit(1)

# Test glitch filter generation
beat_times = [1.0]
result = generate_beat_filter_expression(beat_times, filter_type='glitch', effect_params={'intensity': 0.3})

if result and 'p(X+' in result or 'p(X-' in result:
    print('  ✓ Glitch filter generated with channel shift')
else:
    print(f'  ✗ Glitch filter missing channel shift: {result[:100]}')
    exit(1)

print('✓ All glitch effect tests passed')
exit(0)
"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Glitch effect functional test passed${NC}"
else
    echo -e "${RED}✗ Glitch effect functional test failed${NC}"
    exit 1
fi
echo ""

# Test filter complex generation
echo -e "${YELLOW}Testing filter complex generation...${NC}"
PYTHONPATH=. python3 -c "
from app.services.beat_filters import generate_beat_filter_complex

beat_times = [1.0, 2.0, 3.0]
result = generate_beat_filter_complex(beat_times, filter_type='flash', effect_params={'intensity': 50})

if len(result) == 3:
    print(f'  ✓ Generated {len(result)} filter strings for {len(beat_times)} beats')
else:
    print(f'  ✗ Expected 3 filter strings, got {len(result)}')
    exit(1)

if all('select' in f and 'between(t' in f for f in result):
    print('  ✓ All filters contain time-based selection')
else:
    print('  ✗ Some filters missing time-based selection')
    exit(1)

print('✓ All filter complex tests passed')
exit(0)
"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Filter complex functional test passed${NC}"
else
    echo -e "${RED}✗ Filter complex functional test failed${NC}"
    exit 1
fi
echo ""

# Summary
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}✓ Phase 3.2: All tests passed!${NC}"
echo -e "${BLUE}========================================${NC}"

cd "$PROJECT_ROOT"
deactivate

