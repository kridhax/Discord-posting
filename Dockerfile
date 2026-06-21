FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY . .

# Create logs directory
RUN mkdir -p logs

# Default is web service. Set SERVICE_MODE=worker for Render Background Worker.
CMD ["sh", "render_start.sh"]

