FROM python:3.11-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1

# system deps (kept minimal)
RUN apt-get update && apt-get install -y --no-install-recommends             ffmpeg             && rm -rf /var/lib/apt/lists/*

COPY app/ /app/

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "main:app", "--workers", "1", "--threads", "4"]
