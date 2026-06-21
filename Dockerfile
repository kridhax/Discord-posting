FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY . .

# Create logs directory
RUN mkdir -p logs

CMD ["uvicorn", "web_app:app", "--host", "0.0.0.0", "--port", "10000"]
