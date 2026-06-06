"""Unit tests for the app – run them with: make test"""

from main import APP_VERSION, app

client = app.test_client()


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_api_info_has_pod_and_version():
    data = client.get("/api/info").get_json()
    assert data["pod"]
    assert data["version"] == APP_VERSION


def test_index_page():
    response = client.get("/")
    assert response.status_code == 200
    assert b"Hello from Kubernetes" in response.data
