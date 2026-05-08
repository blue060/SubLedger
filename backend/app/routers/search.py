from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import Subscription, Notification, Category

router = APIRouter(prefix="/api/search", tags=["搜索"], dependencies=[Depends(get_current_user)])


@router.get("")
def search(q: str = Query(default="", min_length=1), db: Session = Depends(get_db)):
    pattern = f"%{q}%"
    subs = db.query(Subscription).filter(Subscription.name.ilike(pattern)).limit(10).all()
    notifs = db.query(Notification).filter(Notification.message.ilike(pattern)).limit(10).all()
    cats = db.query(Category).filter(Category.name.ilike(pattern)).limit(10).all()
    return {
        "subscriptions": [{"id": s.id, "name": s.name, "amount": s.amount, "currency": s.currency} for s in subs],
        "notifications": [{"id": n.id, "message": n.message[:80]} for n in notifs],
        "categories": [{"id": c.id, "name": c.name} for c in cats],
    }