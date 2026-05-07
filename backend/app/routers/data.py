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


def _parse_row(row: dict, row_num: int) -> tuple[Optional[Subscription], Optional[str]]:
    name = str(row.get("name", "")).strip()
    if not name:
        return None, f"第 {row_num} 条：名称为空，已跳过"

    amount = float(row.get("amount", 0) or 0)
    currency = str(row.get("currency", "CNY")).strip()
    billing_cycle = str(row.get("billing_cycle", "monthly")).strip()
    if billing_cycle not in ("monthly", "quarterly", "yearly", "once", "permanent", "custom"):
        return None, f"第 {row_num} 条：未知的计费周期 '{billing_cycle}'，已跳过"

    billing_cycle_num = int(row.get("billing_cycle_num") or 1)
    billing_cycle_unit = str(row.get("billing_cycle_unit", "month")).strip() or "month"

    first_payment_str = str(row.get("first_payment_date", "")).strip()
    first_payment_date = date.fromisoformat(first_payment_str) if first_payment_str else date.today()

    category_id_val = row.get("category_id")
    category_id_int = int(category_id_val) if category_id_val not in (None, "") else None

    next_date = calculate_next_payment_date(
        first_payment_date, billing_cycle,
        billing_cycle_num=billing_cycle_num,
        billing_cycle_unit=billing_cycle_unit,
    )

    expiry_str = str(row.get("expiry_date", "")).strip()
    expiry_date = date.fromisoformat(expiry_str) if expiry_str else None

    intro_amount_val = row.get("intro_amount")
    intro_amount = float(intro_amount_val) if intro_amount_val not in (None, "") else None
    intro_months_val = row.get("intro_months")
    intro_months = int(intro_months_val) if intro_months_val not in (None, "") else None

    notify_val = row.get("notify", True)
    notify = notify_val if isinstance(notify_val, bool) else str(notify_val).strip().lower() in ("true", "1")
    active_val = row.get("is_active", True)
    is_active = active_val if isinstance(active_val, bool) else str(active_val).strip().lower() in ("true", "1")

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
        notes=str(row.get("notes", "")).strip() or None,
        url=str(row.get("url", "")).strip() or None,
        expiry_date=expiry_date,
        payment_method=str(row.get("payment_method", "")).strip() or None,
        intro_amount=intro_amount,
        intro_months=intro_months,
        notify=notify,
        is_active=is_active,
    )
    return sub, None


@router.post("/import")
async def import_data(file: UploadFile = File(...), db: Session = Depends(get_db)):
    content = await file.read()
    text = content.decode("utf-8-sig")

    imported = 0
    skipped = 0
    errors = []

    is_json = file.filename and file.filename.endswith(".json")

    existing_names = {s.name for s in db.query(Subscription.name).all()}

    if is_json:
        data = json.loads(text)
        for i, row in enumerate(data, start=1):
            try:
                sub, err = _parse_row(row, i)
                if err:
                    errors.append(err)
                    skipped += 1
                    continue
                if sub.name in existing_names:
                    errors.append(f"第 {i} 条：'{sub.name}' 已存在，已跳过")
                    skipped += 1
                    continue
                db.add(sub)
                existing_names.add(sub.name)
                imported += 1
            except Exception as e:
                errors.append(f"第 {i} 条：{str(e)}")
                skipped += 1
    else:
        reader = csv.DictReader(io.StringIO(text))
        for row_num, row in enumerate(reader, start=2):
            try:
                sub, err = _parse_row(row, row_num)
                if err:
                    errors.append(err)
                    skipped += 1
                    continue
                if sub.name in existing_names:
                    errors.append(f"第 {row_num} 行：'{sub.name}' 已存在，已跳过")
                    skipped += 1
                    continue
                db.add(sub)
                existing_names.add(sub.name)
                imported += 1
            except Exception as e:
                errors.append(f"第 {row_num} 行：{str(e)}")
                skipped += 1

    db.commit()
    return {"imported": imported, "skipped": skipped, "errors": errors}