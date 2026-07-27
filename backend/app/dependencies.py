import logging

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.security import decode_access_token

logger = logging.getLogger("subledger")


def get_current_user(request: Request, db: Session = Depends(get_db)) -> dict:
    cookie_token = request.cookies.get("subledger_token")
    token = cookie_token
    auth_header = request.headers.get("Authorization", "")
    logger.debug(f"AUTH cookie={'yes' if token else 'no'} header={'yes' if auth_header.startswith('Bearer ') else 'no'} path={request.url.path}")
    if not token:
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="未登录")
    try:
        payload = decode_access_token(token)
    except Exception as e:
        logger.warning(f"JWT decode failed: {type(e).__name__}: {e}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="认证已过期，请重新登录")

    # Cookie-authenticated mutations must always carry the matching CSRF token.
    if cookie_token and request.method in ("POST", "PUT", "PATCH", "DELETE"):
        csrf_header = request.headers.get("X-CSRF-Token", "")
        if not csrf_header or csrf_header != payload.get("csrf", ""):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="CSRF 验证失败")

    try:
        user_id = int(payload["sub"])
    except (KeyError, TypeError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="认证信息无效")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户不存在或已被删除")

    return {
        "user_id": user.id,
        "username": user.username,
        "is_admin": user.is_admin,
        "csrf": payload.get("csrf", ""),
    }


def get_current_user_id(current_user: dict = Depends(get_current_user)) -> int:
    return current_user["user_id"]


def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    if not current_user["is_admin"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅管理员可执行此操作")
    return current_user
