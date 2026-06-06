"""hello-app – a tiny web app that shows which Kubernetes pod answered.

Endpoints:
    /           HTML page with the pod name and the app version
    /api/info   the same information as JSON
    /health     health check used by the Kubernetes probes
"""

import os
import socket
from datetime import datetime, timezone

from flask import Flask, jsonify, render_template_string, request

app = Flask(__name__)

# Set by the Kubernetes Deployment (see k8s/deployment.yaml.j2)
APP_VERSION = os.environ.get("APP_VERSION", "dev")

PAGE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>hello-app {{ version }}</title>
  <style>
    body { margin: 0; min-height: 100vh; display: grid; place-items: center;
           font-family: system-ui, sans-serif; background: #0f172a; color: #e2e8f0; }
    main { background: #1e293b; padding: 2.5rem 3.5rem; border-radius: 16px; text-align: center; }
    .pod { font: 600 1.4rem ui-monospace, monospace; color: #38bdf8; }
    .muted { color: #94a3b8; font-size: .9rem; }
  </style>
</head>
<body>
  <main>
    <h1>Hello from Kubernetes 👋</h1>
    <p>This page was served by pod</p>
    <p class="pod">{{ pod }}</p>
    <p>Version <strong>{{ version }}</strong> · {{ time }}</p>
    <p class="muted">Refresh the page: with several replicas, different pods answer.</p>
  </main>
</body>
</html>"""


def info():
    return {
        "pod": socket.gethostname(),  # inside Kubernetes the hostname is the pod name
        "version": APP_VERSION,
        "time": datetime.now(timezone.utc).strftime("%H:%M:%S UTC"),
    }


@app.get("/")
def index():
    return render_template_string(PAGE, **info())


@app.get("/api/info")
def api_info():
    return jsonify(info())


@app.get("/health")
def health():
    return jsonify(status="ok")


@app.after_request
def log_request(response):
    # One log line per request, so `make logs` shows which pod handled what.
    # Health checks are skipped, otherwise the probes would flood the log.
    if request.path != "/health":
        print(f"{request.method} {request.path} -> {response.status_code}")
    return response


if __name__ == "__main__":
    # Local development only (python app/main.py) – in the container, gunicorn runs the app.
    app.run(port=8000, debug=True)
