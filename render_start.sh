#!/bin/sh
if [ "$SERVICE_MODE" = "worker" ]; then
    echo "Starting Discord bot in worker mode..."
    python app.py
else
    echo "Starting web service..."
    uvicorn web_app:app --host 0.0.0.0 --port 10000
fi
