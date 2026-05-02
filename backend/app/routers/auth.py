from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import User
from app.schemas.auth import LoginRequest, LoginResponse, AuthStatus, SetupRequest
from app.security import verify_password, create_access_token, generate_csrf_token, hash_password

router = APIRouter(prefix="/api/auth", tags=["认证"])


@router.get("/setup-status")
def setup_status(db: Session = Depends(get_db)):
    exists = db.query(User).count() > 0
    return {"needs_setup": not exists}


@router.post("/setup")
def setup(body: SetupRequest, db: Session = Depends(get_db)):
    if db.query(User).count() > 0:
        raise HTTPException(status_code=400, detail="已初始化，不可重复设置")
    if len(body.password) < 4:
        raise HTTPException(status_code=400, detail="密码至少4个字符")
    user = User(username=body.username, password_hash=hash_password(body.password))
    db.add(user)
    db.commit()
    return {"detail": "初始化成功"}


@router.post("/login", response_model=LoginResponse)
def login(body: LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == body.username).first()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误")

    csrf_token = generate_csrf_token()
    jwt_token = create_access_token(user.id, csrf_token)

    response.set_cookie(
        key="subledger_token",
        value=jwt_token,
        httponly=True,
        samesite="lax",
        max_age=7 * 24 * 3600,
    )
    response.set_cookie(
        key="subledger_csrf",
        value=csrf_token,
        httponly=False,
        samesite="lax",
        max_age=7 * 24 * 3600,
    )

    return LoginResponse(username=user.username, token=jwt_token)


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie("subledger_token")
    response.delete_cookie("subledger_csrf")
    return {"detail": "已退出登录"}


@router.get("/me", response_model=AuthStatus)
def me(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == current_user["user_id"]).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户不存在")
    return AuthStatus(user_id=user.id, username=user.username)