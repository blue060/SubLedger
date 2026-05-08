from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import PaymentRecord, Subscription
from app.schemas.payment import PaymentCreate, PaymentUpdate, PaymentOut

router = APIRouter(prefix="/api/payments", tags=["付款记录"], dependencies=[Depends(get_current_user)])


def _record_to_out(record: PaymentRecord) -> PaymentOut:
    out = PaymentOut.model_validate(record)
    if record.subscription:
        out.subscription_name = record.subscription.name
    return out


@router.get("", response_model=list[PaymentOut])
def list_payments(
    subscription_id: int | None = None,
    status: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    q = db.query(PaymentRecord)
    if subscription_id:
        q = q.filter(PaymentRecord.subscription_id == subscription_id)
    if status:
        q = q.filter(PaymentRecord.status == status)
    if start_date:
        q = q.filter(PaymentRecord.payment_date >= start_date)
    if end_date:
        q = q.filter(PaymentRecord.payment_date <= end_date)
    q = q.order_by(PaymentRecord.payment_date.desc())
    return [_record_to_out(r) for r in q.offset((page - 1) * page_size).limit(page_size).all()]


@router.get("/pending", response_model=list[PaymentOut])
def list_pending(db: Session = Depends(get_db)):
    records = db.query(PaymentRecord).filter(
        PaymentRecord.status == "pending"
    ).order_by(PaymentRecord.payment_date.asc()).all()
    return [_record_to_out(r) for r in records]


@router.post("", response_model=PaymentOut, status_code=201)
def create_payment(body: PaymentCreate, db: Session = Depends(get_db)):
    sub = db.query(Subscription).filter(Subscription.id == body.subscription_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="订阅不存在")
    record = PaymentRecord(**body.model_dump())
    db.add(record)
    db.commit()
    db.refresh(record)
    return _record_to_out(record)


@router.put("/{record_id}", response_model=PaymentOut)
def update_payment(record_id: int, body: PaymentUpdate, db: Session = Depends(get_db)):
    record = db.query(PaymentRecord).filter(PaymentRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(record, key, value)
    db.commit()
    db.refresh(record)
    return _record_to_out(record)


@router.post("/{record_id}/confirm")
def confirm_payment(record_id: int, db: Session = Depends(get_db)):
    record = db.query(PaymentRecord).filter(PaymentRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")
    record.status = "confirmed"
    db.commit()
    return {"detail": "已确认付款"}


@router.post("/{record_id}/skip")
def skip_payment(record_id: int, db: Session = Depends(get_db)):
    record = db.query(PaymentRecord).filter(PaymentRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")
    record.status = "skipped"
    db.commit()
    return {"detail": "已跳过付款"}


@router.delete("/{record_id}")
def delete_payment(record_id: int, db: Session = Depends(get_db)):
    record = db.query(PaymentRecord).filter(PaymentRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")
    db.delete(record)
    db.commit()
    return {"detail": "记录已删除"}
