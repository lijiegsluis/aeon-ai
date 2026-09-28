# Aeon Nimbus Intelligence API — event countdowns, insider trades, sentiment, AI predictions.
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Deliberately excludes aeon_intelligence_telegram.session and any *.ini config —
# those hold a live personal Telegram login and must never leave this machine.
# See .dockerignore.
COPY . .

ENV PYTHONUNBUFFERED=1
EXPOSE 8001

CMD ["sh", "-c", "uvicorn intelligence_service:app --host 0.0.0.0 --port ${PORT:-8001}"]
