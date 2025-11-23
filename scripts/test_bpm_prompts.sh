#!/bin/bash

# Helper script to monitor BPM-aware prompt logs in real-time
# Usage: ./scripts/test_bpm_prompts.sh

LOG_FILE="../logs/worker.log"

echo "🔍 Monitoring BPM-Aware Prompt Logs..."
echo "Press Ctrl+C to stop"
echo ""
echo "Looking for:"
echo "  - [PROMPT-ENHANCE] Enhanced prompt with rhythm"
echo "  - [PROMPT-ENHANCE] Tempo descriptor"
echo "  - [PROMPT-ENHANCE] FULL ENHANCED PROMPT"
echo ""
echo "---"

tail -f "$LOG_FILE" | grep --line-buffered -E "PROMPT-ENHANCE|BPM|tempo|slow.*flowing|energetic.*driving|steady.*moderate" -i

