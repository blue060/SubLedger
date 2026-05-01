from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.security import decode_access_token

SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}
SKIP_PATHS = {"/api/auth/login", "/api/health"}


class CSRFMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        if request.method in SAFE_METHODS or request.url.path in SKIP_PATHS:
            return await call_next(request)

        token = request.cookies.get("subledger_token")
        if not token:
            return await call_next(request)

        csrf_header = request.headers.get("X-CSRF-Token", "")
        try:
            payload = decode_access_token(token)
            if csrf_header != payload.get("csrf", ""):
                return Response(
                    content='{"detail":"CSRF 验证失败"}',
                    status_code=403,
                    media_type="application/json",
                )
        except Exception:
            return Response(
                content='{"detail":"认证已过期"}',
                status_code=401,
                media_type="application/json",
            )

        return await call_next(request)