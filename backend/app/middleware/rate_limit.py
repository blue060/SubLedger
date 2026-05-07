from collections import defaultdict
from time import time

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_requests: int = 60, window_seconds: int = 60,
                 login_max_requests: int = 10, login_window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.login_max_requests = login_max_requests
        self.login_window_seconds = login_window_seconds
        self._requests: dict[str, list[float]] = defaultdict(list)
        self._login_requests: dict[str, list[float]] = defaultdict(list)
        self._last_cleanup = 0.0

    def _cleanup(self, ip: str, now: float):
        cutoff = now - self.window_seconds
        self._requests[ip] = [t for t in self._requests[ip] if t > cutoff]

    def _global_cleanup(self, now: float):
        """Remove stale IPs every 60 seconds to prevent memory leak."""
        if now - self._last_cleanup < 60:
            return
        self._last_cleanup = now
        cutoff = now - self.window_seconds
        stale_ips = [
            ip for ip, timestamps in self._requests.items()
            if not timestamps or timestamps[-1] < cutoff
        ]
        for ip in stale_ips:
            del self._requests[ip]

    def _cleanup_login(self, ip: str, now: float):
        cutoff = now - self.login_window_seconds
        self._login_requests[ip] = [t for t in self._login_requests[ip] if t > cutoff]

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.url.path.startswith("/api/health"):
            return await call_next(request)

        ip = request.client.host if request.client else "unknown"
        now = time()

        # Login-specific rate limit
        if request.url.path == "/api/auth/login":
            self._cleanup_login(ip, now)
            if len(self._login_requests[ip]) >= self.login_max_requests:
                return Response(
                    content='{"detail":"登录尝试过于频繁，请稍后再试"}',
                    status_code=429,
                    media_type="application/json",
                )
            self._login_requests[ip].append(now)
            return await call_next(request)

        self._cleanup(ip, now)
        self._global_cleanup(now)

        if len(self._requests[ip]) >= self.max_requests:
            return Response(
                content='{"detail":"请求过于频繁，请稍后再试"}',
                status_code=429,
                media_type="application/json",
            )

        self._requests[ip].append(now)
        return await call_next(request)