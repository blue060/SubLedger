import csv
import io
import json
from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import Subscription
from app.services.billing import calculate_next_payment_date

router = APIRouter(prefix="/api/data", tags=["数据"], dependencies=[Depends(get_current_user)])


@router.get("/export")
def export_data(format: str = "csv", db: Session = Depends(get_db)):
    subscriptions = db.query(Subscription).all()

    if format == "json":
        data = []
        for sub in subscriptions:
            data.append({
                "name": sub.name,
                "amount": sub.amount,
                "currency": sub.currency,
                "billing_cycle": sub.billing_cycle,
                "billing_cycle_num": sub.billing_cycle_num,
                "billing_cycle_unit": sub.billing_cycle_unit,
                "first_payment_date": str(sub.first_payment_date),
                "next_payment_date": str(sub.next_payment_date) if sub.next_payment_date else None,
                "category_id": sub.category_id,
                "notes": sub.notes,
                "url": sub.url,
                "expiry_date": str(sub.expiry_date) if sub.expiry_date else None,
                "payment_method": sub.payment_method,
                "intro_amount": sub.intro_amount,
                "intro_months": sub.intro_months,
                "notify": sub.notify,
                "is_active": sub.is_active,
            })
        content = json.dumps(data, ensure_ascii=False, indent=2)
        return StreamingResponse(
            iter([content]),
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=subscriptions.json"},
        )

    # CSV export
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["name", "amount", "currency", "billing_cycle", "billing_cycle_num", "billing_cycle_unit", "first_payment_date", "next_payment_date", "category_id", "notes", "url", "expiry_date", "payment_method", "intro_amount", "intro_months", "notify", "is_active"])
    for sub in subscriptions:
        writer.writerow([
            sub.name, sub.amount, sub.currency, sub.billing_cycle,
            sub.billing_cycle_num, sub.billing_cycle_unit,
            str(sub.first_payment_date), str(sub.next_payment_date) if sub.next_payment_date else "",
            sub.category_id or "", sub.notes or "", sub.url or "",
            str(sub.expiry_date) if sub.expiry_date else "",
            sub.payment_method or "",
            sub.intro_amount if sub.intro_amount is not None else "",
            sub.intro_months if sub.intro_months is not None else "",
            sub.notify, sub.is_active,
        ])
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=subscriptions.csv"},
    )


@router.post("/import")
async def import_data(file: UploadFile = File(...), db: Session = Depends(get_db)):
    content = await file.read()
    text = content.decode("utf-8-sig")

    reader = csv.DictReader(io.StringIO(text))
    imported = 0
    skipped = 0
    errors = []

    for row_num, row in enumerate(reader, start=2):
        try:
            name = row.get("name", "").strip()
            if not name:
                errors.append(f"第 {row_num} 行：名称为空，已跳过")
                skipped += 1
                continue

            amount = float(row.get("amount", 0))
            currency = row.get("currency", "CNY").strip()
            billing_cycle = row.get("billing_cycle", "monthly").strip()
            if billing_cycle not in ("monthly", "quarterly", "yearly", "once", "permanent", "custom"):
                errors.append(f"第 {row_num} 行：未知的计费周期 '{billing_cycle}'，已跳过")
                skipped += 1
                continue

            billing_cycle_num = int(row.get("billing_cycle_num", "1").strip() or "1")
            billing_cycle_unit = row.get("billing_cycle_unit", "month").strip() or "month"

            first_payment_str = row.get("first_payment_date", "").strip()
            first_payment_date = date.fromisoformat(first_payment_str) if first_payment_str else date.today()

            category_id = row.get("category_id", "").strip()
            category_id_int = int(category_id) if category_id else None

            next_date = calculate_next_payment_date(
                first_payment_date, billing_cycle,
                billing_cycle_num=billing_cycle_num,
                billing_cycle_unit=billing_cycle_unit,
            )

            expiry_str = row.get("expiry_date", "").strip()
            expiry_date = date.fromisoformat(expiry_str) if expiry_str else None

            intro_amount_str = row.get("intro_amount", "").strip()
            intro_amount = float(intro_amount_str) if intro_amount_str else None
            intro_months_str = row.get("intro_months", "").strip()
            intro_months = int(intro_months_str) if intro_months_str else None

            sub = Subscription(
                name=name,
                amount=amount,
                currency=currency,
                billing_cycle=billing_cycle,
                billing_cycle_num=billing_cycle_num,
                billing_cycle_unit=billing_cycle_unit,
                first_payment_date=first_payment_date,
                next_payment_date=next_date,
                category_id=category_id_int,
                notes=row.get("notes", "").strip() or None,
                url=row.get("url", "").strip() or None,
                expiry_date=expiry_date,
                payment_method=row.get("payment_method", "").strip() or None,
                intro_amount=intro_amount,
                intro_months=intro_months,
                notify=row.get("notify", "true").strip().lower() in ("true", "1"),
                is_active=row.get("is_active", "true").strip().lower() in ("true", "1"),
            )
            db.add(sub)
            imported += 1
        except Exception as e:
            errors.append(f"第 {row_num} 行：{str(e)}")
            skipped += 1

    db.commit()
    return {"imported": imported, "skipped": skipped, "errors": errors}