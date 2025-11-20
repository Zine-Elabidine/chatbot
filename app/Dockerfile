FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Use app folder as build context (set in docker-compose)
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application sources from current app directory
COPY main.py ./
COPY agent.py ./
COPY session_manager.py ./
COPY config.py ./
COPY news_store.py ./
COPY index.html ./

EXPOSE 8000

ENV PORT=8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
