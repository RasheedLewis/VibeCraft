#!/bin/bash

# Helper script to monitor BPM-aware prompt logs in real-time
# Usage: ./scripts/test_bpm_prompts.sh

LOG_DIR="../logs"
LOG_FILE="${LOG_DIR}/worker.log"

echo "🔍 Monitoring BPM-Aware Prompt Logs..."
echo "Press Ctrl+C to stop"
echo ""
echo "Looking for:"
echo "  - [PROMPT-ENHANCE] Enhanced prompt with rhythm"
echo "  - [PROMPT-ENHANCE] Tempo descriptor"
echo "  - [PROMPT-ENHANCE] FULL ENHANCED PROMPT"
echo ""
echo "---"

# Check if multiple worker logs exist (worker.log.1, worker.log.2, etc.)
if ls "${LOG_DIR}"/worker.log.* 1> /dev/null 2>&1; then
    # Multiple workers: tail all worker logs
    echo "📋 Monitoring all worker logs (multiple workers detected)..."
    tail -f "${LOG_DIR}"/worker.log.* | grep --line-buffered -E "PROMPT-ENHANCE|BPM|tempo|slow.*flowing|energetic.*driving|steady.*moderate" -i
else
    # Single worker: use worker.log
    tail -f "$LOG_FILE" | grep --line-buffered -E "PROMPT-ENHANCE|BPM|tempo|slow.*flowing|energetic.*driving|steady.*moderate" -i
fi

