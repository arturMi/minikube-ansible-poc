# Image for hello-app: a slim Python base image + the app, served by gunicorn as a non-root user.
FROM python:3.13-slim

# No .pyc files, and unbuffered output so logs show up immediately in `kubectl logs`
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install the dependencies first: Docker caches this layer until requirements.txt changes
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .

# Don't run as root inside the container
RUN useradd --uid 10001 appuser
USER 10001

EXPOSE 8000
# --no-control-socket: gunicorn's admin socket isn't needed in a container (Kubernetes manages the process)
CMD ["gunicorn", "--bind=0.0.0.0:8000", "--workers=2", "--no-control-socket", "main:app"]
