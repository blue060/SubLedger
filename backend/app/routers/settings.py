from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import AppSettings
from app.schemas.settings import SettingsOut, SettingsUpdate, PasswordChange
from app.security import verify_password, hash_password

router = APIRouter(prefix="/api/settings", tags=["设置"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=SettingsOut)
def get_settings(db: Session = Depends(get_db)):
    settings = db.query(AppSettings).filter(AppSettings.id == 1).first()
    if not settings:
        raise HTTPException(status_code=404, detail="设置不存在")
    return SettingsOut(
        preferred_currency=settings.preferred_currency,
        reminder_days=settings.reminder_days,
        monthly_budget=settings.monthly_budget,
        theme=settings.theme,
        smtp_host=settings.smtp_host,
        smtp_port=settings.smtp_port,
        smtp_user=settings.smtp_user,
        smtp_tls=settings.smtp_tls,
        bark_url=settings.bark_url,
        serverchan_key=settings.serverchan_key,
    )


@router.put("", response_model=SettingsOut)
def update_settings(body: SettingsUpdate, db: Session = Depends(get_db)):
    settings = db.query(AppSettings).filter(AppSettings.id == 1).first()
    if not settings:
        raise HTTPException(status_code=404, detail="设置不存在")

    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(settings, key, value)
    db.commit()
    db.refresh(settings)

    return SettingsOut(
        preferred_currency=settings.preferred_currency,
        reminder_days=settings.reminder_days,
        monthly_budget=settings.monthly_budget,
        theme=settings.theme,
        smtp_host=settings.smtp_host,
        smtp_port=settings.smtp_port,
        smtp_user=settings.smtp_user,
        smtp_tls=settings.smtp_tls,
        bark_url=settings.bark_url,
        serverchan_key=settings.serverchan_key,
    )


@router.post("/password")
def change_password(body: PasswordChange, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    from app.models import User

    user = db.query(User).filter(User.id == current_user["user_id"]).first()
    if not user or not verify_password(body.old_password, user.password_hash):
        raise HTTPException(status_code=400, detail="原密码错误")

    user.password_hash = hash_password(body.new_password)
    db.commit()
    return {"detail": "密码修改成功"}


@router.post("/test-email")
async def test_email(db: Session = Depends(get_db)):
    from app.services.notifier import Notifier

    settings = db.query(AppSettings).filter(AppSettings.id == 1).first()
    if not settings or not settings.smtp_host:
        raise HTTPException(status_code=400, detail="未配置 SMTP")

    notifier = Notifier()
    try:
        await notifier.send_email(
            subject="SubLedger 测试邮件",
            body="如果您收到此邮件，说明邮件通知配置成功！",
            settings=settings,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"邮件发送失败: {str(e)}")

    return {"detail": "测试邮件已发送"}


@router.post("/test-push")
async def test_push(db: Session = Depends(get_db)):
    from app.services.notifier import Notifier

    settings = db.query(AppSettings).filter(AppSettings.id == 1).first()
    if not settings:
        raise HTTPException(status_code=404, detail="设置不存在")

    notifier = Notifier()
    if settings.bark_url:
        await notifier.send_bark("SubLedger 测试", "如果您收到此推送，说明 Bark 配置成功！", settings.bark_url)
    elif settings.serverchan_key:
        await notifier.send_serverchan("SubLedger 测试", "如果您收到此推送，说明 Server酱 配置成功！", settings.serverchan_key)
    else:
        raise HTTPException(status_code=400, detail="未配置推送渠道")

    return {"detail": "测试推送已发送"}