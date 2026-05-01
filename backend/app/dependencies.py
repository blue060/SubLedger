from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.security import decode_access_token


def get_current_user(request: Request, db: Session = Depends(get_db)) -> dict:
    token = request.cookies.get("subledger_token")
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="未登录")
    try:
        payload = decode_access_token(token)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="认证已过期，请重新登录")

    return {"user_id": payload["sub"], "csrf": payload.get("csrf", "")}