#!/bin/bash
# Self-healing retry script with exponential backoff

COMMAND="$1"
MAX_RETRIES=${2:-3}
DELAY=${3:-5}

echo " Starting retry mechanism for: $COMMAND"

for i in $(seq 1 $MAX_RETRIES); do
    echo " Attempt $i of $MAX_RETRIES"
    if eval "$COMMAND"; then
        echo " Command succeeded on attempt $i!"
        exit 0
    else
        echo " Attempt $i failed"
        if [ $i -eq $MAX_RETRIES ]; then
            echo "💀 All $MAX_RETRIES attempts failed."
            exit 1
        fi
        echo " Waiting $DELAY seconds before retry..."
        sleep $DELAY
        DELAY=$((DELAY * 2))  # Exponential backoff
    fi
done