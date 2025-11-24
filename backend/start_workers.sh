#!/bin/sh
# Start multiple RQ workers for parallel processing
# This script starts NUM_WORKERS processes (default: 4)

NUM_WORKERS=${NUM_WORKERS:-4}

echo "Starting ${NUM_WORKERS} RQ workers for parallel processing..."

# Start workers in background
for i in $(seq 1 ${NUM_WORKERS}); do
    echo "Starting worker ${i}..."
    rq worker ai_music_video --url "$REDIS_URL" &
done

# Wait for all background processes
wait

