from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app

client = TestClient(app)


def preflight(origin):
    return client.options(
        "/api/auth/login",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "authorization,content-type",
        },
    )


def test_frontend_origin_is_allowed():
    response = preflight(settings.frontend_origin)

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == settings.frontend_origin
    assert "authorization" in response.headers["access-control-allow-headers"].lower()


def test_other_origins_get_no_cors_headers():
    response = preflight("http://evil.example.com")

    assert "access-control-allow-origin" not in response.headers
