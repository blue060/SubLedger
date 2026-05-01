from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import Notification
from app.schemas.notification import NotificationOut, UnreadCount

router = APIRouter(prefix="/api/notifications", tags=["通知"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=list[NotificationOut])
def list_notifications(unread_only: bool = False, db: Session = Depends(get_db)):
    q = db.query(Notification).order_by(Notification.notify_date.desc())
    if unread_only:
        q = q.filter(Notification.is_read == False)
    return q.all()


@router.get("/unread-count", response_model=UnreadCount)
def unread_count(db: Session = Depends(get_db)):
    count = db.query(Notification).filter(Notification.is_read == False).count()
    return UnreadCount(count=count)


@router.patch("/{notification_id}", response_model=NotificationOut)
def mark_read(notification_id: int, db: Session = Depends(get_db)):
    n = db.query(Notification).filter(Notification.id == notification_id).first()
    if not n:
        raise HTTPException(status_code=404, detail="通知不存在")
    n.is_read = True
    db.commit()
    db.refresh(n)
    return n


@router.post("/mark-all-read")
def mark_all_read(db: Session = Depends(get_db)):
    db.query(Notification).filter(Notification.is_read == False).update({"is_read": True})
    db.commit()
    return {"detail": "全部标记已读"}