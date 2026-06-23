FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source packages explicitly
COPY utils/ ./utils/
COPY facebook/ ./facebook/
COPY discord_listener/ ./discord_listener/
COPY logger/ ./logger/
COPY formatter/ ./formatter/
COPY config.py handlers.py app.py web_app.py token_app.py token_refresh.py render_start.sh ./

# Create logs directory
RUN mkdir -p logs

# Default is web service. Set SERVICE_MODE=worker for Render Background Worker.
# Set SERVICE_MODE=token for the standalone token generator UI.
CMD ["sh", "render_start.sh"]
