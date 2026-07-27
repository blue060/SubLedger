import os

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.dependencies import require_admin
from app.models import User
from app.schemas.user import PasswordReset, UserCreate, UserOut
from app.security import hash_password
from app.services.user_provisioning import ensure_user_workspace


router = APIRouter(prefix="/api/users", tags=["用户"], dependencies=[Depends(require_admin)])


@router.get("", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db)):
    return db.query(User).order_by(User.id).all()


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(body: UserCreate, db: Session = Depends(get_db)):
    if db.query(User.id).filter(User.username == body.username).first():
        raise HTTPException(status_code=409, detail="用户名已存在")

    user = User(
        username=body.username,
        password_hash=hash_password(body.password),
        is_admin=body.is_admin,
    )
    db.add(user)
    try:
        db.flush()
        app_config = get_settings()
        ensure_user_workspace(
            db,
            user.id,
            preferred_currency=app_config.DEFAULT_CURRENCY,
            reminder_days=app_config.REMINDER_DAYS,
        )
        db.commit()
        db.refresh(user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="用户名已存在")
    return user


@router.post("/{user_id}/reset-password")
def reset_password(user_id: int, body: PasswordReset, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    user.password_hash = hash_password(body.new_password)
    db.commit()
    return {"detail": "密码已重置"}


@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    if user.id == current_user["user_id"]:
        raise HTTPException(status_code=400, detail="不能删除当前登录用户")
    if user.is_admin and db.query(User).filter(User.is_admin == True).count() <= 1:
        raise HTTPException(status_code=400, detail="不能删除最后一个管理员")

    backup_paths = [record.file_path for record in user.backup_records]
    db.delete(user)
    db.commit()
    for path in backup_paths:
        if os.path.exists(path):
            try:
                os.remove(path)
            except OSError:
                pass
    return {"detail": "用户及其个人数据已删除"}
