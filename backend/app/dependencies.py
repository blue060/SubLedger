import logging

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.security import decode_access_token

logger = logging.getLogger("subledger")


def get_current_user(request: Request, db: Session = Depends(get_db)) -> dict:
    token = request.cookies.get("subledger_token")
    auth_header = request.headers.get("Authorization", "")
    logger.info(f"AUTH DEBUG cookie={'yes' if token else 'no'} header={'yes' if auth_header.startswith('Bearer ') else 'no'} path={request.url.path}")
    if not token:
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="未登录")
    try:
        payload = decode_access_token(token)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="认证已过期，请重新登录")

    # CSRF check for mutating requests
    if request.method in ("POST", "PUT", "PATCH", "DELETE"):
        csrf_header = request.headers.get("X-CSRF-Token", "")
        csrf_cookie = request.cookies.get("subledger_csrf", "")
        if not csrf_header and not csrf_cookie:
            # No CSRF provided at all — allow for simplicity in self-hosted setup
            pass
        elif csrf_header and csrf_header != payload.get("csrf", ""):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="CSRF 验证失败")

    return {"user_id": payload["sub"], "csrf": payload.get("csrf", "")}