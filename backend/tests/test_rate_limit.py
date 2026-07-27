from fastapi import FastAPI, Response
from fastapi.testclient import TestClient

from app.middleware.rate_limit import RateLimitMiddleware


def _client() -> TestClient:
    app = FastAPI()
    app.add_middleware(
        RateLimitMiddleware,
        max_requests=2,
        window_seconds=60,
        login_max_requests=2,
        login_window_seconds=60,
    )

    @app.get("/api/data")
    def read_data():
        return {"ok": True}

    @app.post("/api/data")
    def write_data():
        return {"ok": True}

    @app.post("/api/auth/login")
    def login(success: bool = False):
        if success:
            return {"ok": True}
        return Response(status_code=401)

    return TestClient(app)


def test_read_only_navigation_is_not_rate_limited():
    client = _client()
    assert all(client.get("/api/data").status_code == 200 for _ in range(10))


def test_mutations_are_rate_limited_with_retry_header():
    client = _client()
    assert client.post("/api/data").status_code == 200
    assert client.post("/api/data").status_code == 200
    response = client.post("/api/data")
    assert response.status_code == 429
    assert response.headers["retry-after"] == "60"


def test_only_failed_logins_count_and_success_resets_failures():
    client = _client()
    assert client.post("/api/auth/login").status_code == 401
    assert client.post("/api/auth/login?success=true").status_code == 200
    assert client.post("/api/auth/login").status_code == 401
    assert client.post("/api/auth/login").status_code == 401
    response = client.post("/api/auth/login")
    assert response.status_code == 429
