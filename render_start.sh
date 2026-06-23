#!/bin/sh
set -e

echo "SERVICE_MODE=$SERVICE_MODE"
echo "MAPPINGS_JSON length=${#MAPPINGS_JSON}"

if [ -n "$MAPPINGS_JSON" ]; then
    echo "Writing mappings.json from environment variable..."
    printf '%s\n' "$MAPPINGS_JSON" > /app/mappings.json
    echo "Wrote /app/mappings.json ($(wc -c < /app/mappings.json) bytes)"
else
    echo "MAPPINGS_JSON not set, relying on existing /app/mappings.json"
fi

if [ "$SERVICE_MODE" = "token" ]; then
    echo "Starting token generator service..."
    uvicorn token_app:app --host 0.0.0.0 --port 10000
elif [ "$SERVICE_MODE" = "worker" ]; then
    echo "Starting Discord bot in worker mode..."
    python app.py
else
    echo "Starting web service..."
    uvicorn web_app:app --host 0.0.0.0 --port 10000
fi
