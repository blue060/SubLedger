from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import Subscription, Category
from app.schemas.subscription import SubscriptionCreate, SubscriptionUpdate, SubscriptionOut
from app.services.billing import calculate_next_payment_date

router = APIRouter(prefix="/api/subscriptions", tags=["订阅"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=list[SubscriptionOut])
def list_subscriptions(
    is_active: bool | None = None,
    db: Session = Depends(get_db),
):
    q = db.query(Subscription)
    if is_active is not None:
        q = q.filter(Subscription.is_active == is_active)
    subs = q.order_by(Subscription.next_payment_date).all()
    result = []
    for s in subs:
        out = SubscriptionOut.model_validate(s)
        if s.category:
            out.category_name = s.category.name
            out.category_color = s.category.color
        result.append(out)
    return result


@router.post("", response_model=SubscriptionOut, status_code=status.HTTP_201_CREATED)
def create_subscription(body: SubscriptionCreate, db: Session = Depends(get_db)):
    if body.category_id:
        cat = db.query(Category).filter(Category.id == body.category_id).first()
        if not cat:
            raise HTTPException(status_code=400, detail="分类不存在")

    next_date = calculate_next_payment_date(body.first_payment_date, body.billing_cycle)

    sub = Subscription(
        **body.model_dump(),
        next_payment_date=next_date,
    )
    db.add(sub)
    db.commit()
    db.refresh(sub)

    out = SubscriptionOut.model_validate(sub)
    if sub.category:
        out.category_name = sub.category.name
        out.category_color = sub.category.color
    return out


@router.get("/{sub_id}", response_model=SubscriptionOut)
def get_subscription(sub_id: int, db: Session = Depends(get_db)):
    sub = db.query(Subscription).filter(Subscription.id == sub_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="订阅不存在")
    out = SubscriptionOut.model_validate(sub)
    if sub.category:
        out.category_name = sub.category.name
        out.category_color = sub.category.color
    return out


@router.put("/{sub_id}", response_model=SubscriptionOut)
def update_subscription(sub_id: int, body: SubscriptionUpdate, db: Session = Depends(get_db)):
    sub = db.query(Subscription).filter(Subscription.id == sub_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="订阅不存在")

    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(sub, key, value)

    # Recalculate next_payment_date if relevant fields changed
    if any(k in update_data for k in ("first_payment_date", "billing_cycle")):
        sub.next_payment_date = calculate_next_payment_date(
            sub.first_payment_date, sub.billing_cycle
        )

    db.commit()
    db.refresh(sub)

    out = SubscriptionOut.model_validate(sub)
    if sub.category:
        out.category_name = sub.category.name
        out.category_color = sub.category.color
    return out


@router.delete("/{sub_id}")
def delete_subscription(sub_id: int, db: Session = Depends(get_db)):
    sub = db.query(Subscription).filter(Subscription.id == sub_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="订阅不存在")
    db.delete(sub)
    db.commit()
    return {"detail": "订阅已删除"}