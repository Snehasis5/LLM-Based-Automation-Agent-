# Dockerfile
FROM python:3.11-slim-buster
RUN apt-get update && apt-get install -y git && apt-get clean
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./app /app

# Install uv
RUN pip install uv

# Make sure /data exists
RUN mkdir -p /data
VOLUME /data

# Install ffmpeg for whisper
RUN apt-get update && apt-get install -y ffmpeg libsndfile1 --no-install-recommends && rm -rf /var/lib/apt/lists/*

EXPOSE 8000

#CMD ["uv", "run", "api:app", "--host", " 127.0.0.1", "--port", "8000"] # Using uvicorn
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
