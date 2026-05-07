import logging
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query, Body, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import Subscription, Category, PriceHistory
from app.schemas.subscription import SubscriptionCreate, SubscriptionUpdate, SubscriptionOut
from app.schemas.price_history import PriceHistoryOut
from app.services.billing import calculate_next_payment_date

logger = logging.getLogger("subledger")

router = APIRouter(prefix="/api/subscriptions", tags=["订阅"], dependencies=[Depends(get_current_user)])


def _sub_to_out(sub: Subscription) -> SubscriptionOut:
    out = SubscriptionOut.model_validate(sub)
    if sub.category:
        out.category_name = sub.category.name
        out.category_color = sub.category.color
    if sub.expiry_date:
        out.remaining_days = (sub.expiry_date - date.today()).days
    return out


@router.get("", response_model=list[SubscriptionOut])
def list_subscriptions(
    is_active: bool | None = None,
    search: str | None = None,
    category_id: int | None = None,
    currency: str | None = None,
    db: Session = Depends(get_db),
):
    q = db.query(Subscription)
    if is_active is not None:
        q = q.filter(Subscription.is_active == is_active)
    if search:
        q = q.filter(Subscription.name.ilike(f"%{search}%"))
    if category_id is not None:
        q = q.filter(Subscription.category_id == category_id)
    if currency:
        q = q.filter(Subscription.currency == currency)
    subs = q.order_by(Subscription.next_payment_date.asc().nulls_last()).all()
    return [_sub_to_out(s) for s in subs]


@router.post("", response_model=SubscriptionOut, status_code=status.HTTP_201_CREATED)
def create_subscription(body: SubscriptionCreate, db: Session = Depends(get_db)):
    if body.category_id:
        cat = db.query(Category).filter(Category.id == body.category_id).first()
        if not cat:
            raise HTTPException(status_code=400, detail="分类不存在")

    next_date = calculate_next_payment_date(
        body.first_payment_date, body.billing_cycle,
        billing_cycle_num=body.billing_cycle_num,
        billing_cycle_unit=body.billing_cycle_unit,
    )

    sub = Subscription(
        **body.model_dump(),
        next_payment_date=next_date,
    )
    db.add(sub)
    db.commit()
    db.refresh(sub)
    return _sub_to_out(sub)


@router.get("/{sub_id}", response_model=SubscriptionOut)
def get_subscription(sub_id: int, db: Session = Depends(get_db)):
    sub = db.query(Subscription).filter(Subscription.id == sub_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="订阅不存在")
    return _sub_to_out(sub)


@router.get("/{sub_id}/price-history", response_model=list[PriceHistoryOut])
def get_price_history(sub_id: int, db: Session = Depends(get_db)):
    sub = db.query(Subscription).filter(Subscription.id == sub_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="订阅不存在")
    return db.query(PriceHistory).filter(
        PriceHistory.subscription_id == sub_id
    ).order_by(PriceHistory.created_at.desc()).all()


def _apply_update(sub: Subscription, body: SubscriptionUpdate, db: Session) -> Subscription:
    update_data = body.model_dump(exclude_unset=True)

    for nullable_key in ("billing_cycle_num", "billing_cycle_unit"):
        if nullable_key in update_data and update_data[nullable_key] is None:
            del update_data[nullable_key]

    if "amount" in update_data or "currency" in update_data:
        old_amount = sub.amount
        old_currency = sub.currency
        new_amount = update_data.get("amount", old_amount)
        new_currency = update_data.get("currency", old_currency)
        if old_amount != new_amount or old_currency != new_currency:
            db.add(PriceHistory(
                subscription_id=sub.id,
                old_amount=old_amount,
                new_amount=new_amount,
                old_currency=old_currency,
                new_currency=new_currency,
            ))

    for key, value in update_data.items():
        setattr(sub, key, value)

    if any(k in update_data for k in ("first_payment_date", "billing_cycle", "billing_cycle_num", "billing_cycle_unit")):
        sub.next_payment_date = calculate_next_payment_date(
            sub.first_payment_date, sub.billing_cycle,
            billing_cycle_num=sub.billing_cycle_num,
            billing_cycle_unit=sub.billing_cycle_unit,
        )

    db.commit()
    db.refresh(sub)
    return sub


@router.put("/{sub_id}", response_model=SubscriptionOut)
def update_subscription(sub_id: int, body: SubscriptionUpdate, db: Session = Depends(get_db)):
    sub = db.query(Subscription).filter(Subscription.id == sub_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="订阅不存在")

    try:
        _apply_update(sub, body, db)
        return _sub_to_out(sub)
    except Exception as e:
        logger.exception(f"更新订阅失败: sub_id={sub_id}, update_data={body.model_dump(exclude_unset=True)}")
        raise HTTPException(status_code=500, detail=f"更新订阅失败: {e}")


@router.patch("/{sub_id}", response_model=SubscriptionOut)
def patch_subscription(sub_id: int, body: SubscriptionUpdate, db: Session = Depends(get_db)):
    sub = db.query(Subscription).filter(Subscription.id == sub_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="订阅不存在")

    try:
        _apply_update(sub, body, db)
        return _sub_to_out(sub)
    except Exception as e:
        logger.exception(f"更新订阅失败: sub_id={sub_id}, update_data={body.model_dump(exclude_unset=True)}")
        raise HTTPException(status_code=500, detail=f"更新订阅失败: {e}")


@router.delete("/{sub_id}")
def delete_subscription(sub_id: int, db: Session = Depends(get_db)):
    sub = db.query(Subscription).filter(Subscription.id == sub_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="订阅不存在")
    db.delete(sub)
    db.commit()
    return {"detail": "订阅已删除"}


@router.post("/batch-delete")
def batch_delete(ids: list[int] = Body(..., embed=True), db: Session = Depends(get_db)):
    db.query(Subscription).filter(Subscription.id.in_(ids)).delete(synchronize_session=False)
    db.commit()
    return {"detail": f"已删除 {len(ids)} 个订阅"}


@router.post("/batch-toggle")
def batch_toggle(ids: list[int] = Body(..., embed=True), is_active: bool = Body(..., embed=True), db: Session = Depends(get_db)):
    db.query(Subscription).filter(Subscription.id.in_(ids)).update(
        {"is_active": is_active}, synchronize_session=False
    )
    db.commit()
    return {"detail": f"已更新 {len(ids)} 个订阅"}
