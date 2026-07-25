from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.middleware.rate_limit import RateLimitMiddleware


def test_login_rate_limit_blocks_repeated_attempts():
    app = FastAPI()
    app.add_middleware(
        RateLimitMiddleware,
        max_requests=100,
        login_max_requests=2,
        login_window_seconds=60,
    )

    @app.post("/api/auth/login")
    def login():
        return {"ok": True}

    with TestClient(app) as client:
        assert client.post("/api/auth/login").status_code == 200
        assert client.post("/api/auth/login").status_code == 200
        response = client.post("/api/auth/login")

    assert response.status_code == 429
    assert response.json()["detail"] == "登录尝试过于频繁，请稍后再试"


def test_rate_limit_does_not_count_frontend_assets():
    app = FastAPI()
    app.add_middleware(RateLimitMiddleware, max_requests=1)

    @app.get("/assets/app.js")
    def asset():
        return {"ok": True}

    with TestClient(app) as client:
        assert client.get("/assets/app.js").status_code == 200
        assert client.get("/assets/app.js").status_code == 200
