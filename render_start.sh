#!/bin/sh
set -e

echo "SERVICE_MODE=$SERVICE_MODE"

# Render mounts Secret Files at /etc/secrets/<filename>
if [ -f /etc/secrets/mappings.json ]; then
    echo "Found Render secret file at /etc/secrets/mappings.json, copying to /app..."
    cp /etc/secrets/mappings.json /app/mappings.json
    echo "Copied /app/mappings.json ($(wc -c < /app/mappings.json) bytes)"
elif [ -n "$MAPPINGS_JSON_B64" ]; then
    echo "Writing mappings.json from base64 environment variable..."
    printf '%s\n' "$MAPPINGS_JSON_B64" | base64 -d > /app/mappings.json
    echo "Wrote /app/mappings.json ($(wc -c < /app/mappings.json) bytes)"
elif [ -n "$MAPPINGS_JSON" ]; then
    echo "Writing mappings.json from environment variable..."
    printf '%s\n' "$MAPPINGS_JSON" > /app/mappings.json
    echo "Wrote /app/mappings.json ($(wc -c < /app/mappings.json) bytes)"
else
    echo "No mappings source found, relying on existing /app/mappings.json"
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
