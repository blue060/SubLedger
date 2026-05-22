from datetime import date
from dateutil.relativedelta import relativedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import Subscription, Category, AppSettings
from app.schemas.analytics import MonthlyComparison, CategoryTrendItem, TopSubscription, CurrencyBreakdownItem, AnnualReport
from app.services.exchange_rate import exchange_rate_service
from app.services.billing import calculate_monthly_projection, _effective_amount

router = APIRouter(prefix="/api/analytics", tags=["支出分析"], dependencies=[Depends(get_current_user)])


@router.get("/monthly-comparison", response_model=MonthlyComparison)
async def monthly_comparison(db: Session = Depends(get_db)):
    settings = db.query(AppSettings).filter(AppSettings.id == 1).first()
    preferred = settings.preferred_currency if settings else "CNY"

    today = date.today()
    current_month = today.replace(day=1)
    last_month = current_month - relativedelta(months=1)

    subscriptions = db.query(Subscription).filter(Subscription.is_active == True).all()

    current_total = 0.0
    last_total = 0.0
    current_by_cur: dict[str, float] = {}
    last_by_cur: dict[str, float] = {}

    for sub in subscriptions:
        proj_current = calculate_monthly_projection(sub, current_month)
        if proj_current is not None:
            current_by_cur[sub.currency] = current_by_cur.get(sub.currency, 0) + proj_current

        proj_last = calculate_monthly_projection(sub, last_month)
        if proj_last is not None:
            last_by_cur[sub.currency] = last_by_cur.get(sub.currency, 0) + proj_last

    for cur, amt in current_by_cur.items():
        current_total += await exchange_rate_service.convert(db, amt, cur, preferred)
    for cur, amt in last_by_cur.items():
        last_total += await exchange_rate_service.convert(db, amt, cur, preferred)

    current_total = round(current_total, 2)
    last_total = round(last_total, 2)

    return MonthlyComparison(
        current_month=current_total,
        last_month=last_total,
        change=round(current_total - last_total, 2),
        currency=preferred,
    )


@router.get("/category-trend", response_model=list[CategoryTrendItem])
async def category_trend(months: int = Query(default=12, ge=1, le=24), db: Session = Depends(get_db)):
    settings = db.query(AppSettings).filter(AppSettings.id == 1).first()
    preferred = settings.preferred_currency if settings else "CNY"

    subscriptions = db.query(Subscription).filter(Subscription.is_active == True).all()
    categories = db.query(Category).all()
    cat_map = {c.id: c for c in categories}

    today = date.today()
    result = []

    for i in range(months - 1, -1, -1):
        m = today - relativedelta(months=i)
        target = m.replace(day=1)
        month_str = target.strftime("%Y-%m")

        cat_amounts: dict[str, float] = {}
        for sub in subscriptions:
            proj = calculate_monthly_projection(sub, target)
            if proj is None:
                continue
            cat_name = cat_map[sub.category_id].name if sub.category_id and sub.category_id in cat_map else "未分类"
            converted = await exchange_rate_service.convert(db, proj, sub.currency, preferred)
            cat_amounts[cat_name] = round(cat_amounts.get(cat_name, 0) + converted, 2)

        result.append(CategoryTrendItem(month=month_str, categories=cat_amounts))

    return result


@router.get("/top-subscriptions", response_model=list[TopSubscription])
async def top_subscriptions(limit: int = Query(default=10, ge=1, le=50), db: Session = Depends(get_db)):
    settings = db.query(AppSettings).filter(AppSettings.id == 1).first()
    preferred = settings.preferred_currency if settings else "CNY"

    subscriptions = db.query(Subscription).filter(Subscription.is_active == True).all()
    categories = db.query(Category).all()
    cat_map = {c.id: c for c in categories}

    items = []
    for sub in subscriptions:
        current_month = date.today().replace(day=1)
        proj = calculate_monthly_projection(sub, current_month)
        if proj is None:
            yearly = sub.amount * 12  # fallback for once/permanent
            if sub.billing_cycle == "yearly":
                yearly = sub.amount
            elif sub.billing_cycle == "quarterly":
                yearly = sub.amount * 4
            elif sub.billing_cycle == "monthly":
                yearly = sub.amount * 12
            else:
                yearly = sub.amount
        else:
            # annualize monthly projection
            if sub.billing_cycle == "yearly":
                yearly = proj
            elif sub.billing_cycle == "quarterly":
                yearly = proj * 4
            else:
                yearly = proj * 12

        converted_yearly = await exchange_rate_service.convert(db, yearly, sub.currency, preferred)

        cat = cat_map.get(sub.category_id) if sub.category_id else None
        items.append(TopSubscription(
            id=sub.id,
            name=sub.name,
            amount=sub.amount,
            currency=sub.currency,
            converted_amount=round(converted_yearly, 2),
            category_name=cat.name if cat else None,
            category_color=cat.color if cat else None,
        ))

    items.sort(key=lambda x: x.converted_amount, reverse=True)
    return items[:limit]


@router.get("/currency-breakdown", response_model=list[CurrencyBreakdownItem])
async def currency_breakdown(db: Session = Depends(get_db)):
    settings = db.query(AppSettings).filter(AppSettings.id == 1).first()
    preferred = settings.preferred_currency if settings else "CNY"

    subscriptions = db.query(Subscription).filter(Subscription.is_active == True).all()

    current_month = date.today().replace(day=1)
    by_currency: dict[str, dict] = {}

    for sub in subscriptions:
        proj = calculate_monthly_projection(sub, current_month)
        if proj is None:
            continue
        if sub.currency not in by_currency:
            by_currency[sub.currency] = {"count": 0, "total": 0.0}
        by_currency[sub.currency]["count"] += 1
        by_currency[sub.currency]["total"] += proj

    result = []
    for cur, data in by_currency.items():
        converted = await exchange_rate_service.convert(db, data["total"], cur, preferred)
        result.append(CurrencyBreakdownItem(
            currency=cur,
            count=data["count"],
            total_amount=round(data["total"], 2),
            converted_amount=round(converted, 2),
        ))

    result.sort(key=lambda x: x.converted_amount, reverse=True)
    return result


@router.get("/annual-report", response_model=AnnualReport)
async def annual_report(year: int = Query(default=date.today().year, ge=2020, le=2030), db: Session = Depends(get_db)):
    settings = db.query(AppSettings).filter(AppSettings.id == 1).first()
    preferred = settings.preferred_currency if settings else "CNY"

    subscriptions = db.query(Subscription).filter(Subscription.is_active == True).all()
    categories = db.query(Category).all()
    cat_map = {c.id: c for c in categories}

    monthly_totals = []
    grand_total = 0.0

    for month in range(1, 13):
        target = date(year, month, 1)
        month_total = 0.0
        for sub in subscriptions:
            proj = calculate_monthly_projection(sub, target)
            if proj is None:
                continue
            converted = await exchange_rate_service.convert(db, proj, sub.currency, preferred)
            month_total += converted
        monthly_totals.append({"month": f"{year}-{month:02d}", "total": round(month_total, 2)})
        grand_total += month_total

    # Category totals based on current month projection annualized
    cat_totals: dict[str, dict] = {}
    for sub in subscriptions:
        current_month = date.today().replace(day=1)
        proj = calculate_monthly_projection(sub, current_month)
        if proj is None:
            continue
        converted = await exchange_rate_service.convert(db, proj, sub.currency, preferred)
        annualized = converted * 12
        cat_name = cat_map[sub.category_id].name if sub.category_id and sub.category_id in cat_map else "未分类"
        cat_color = cat_map[sub.category_id].color if sub.category_id and sub.category_id in cat_map else "#909399"
        if cat_name not in cat_totals:
            cat_totals[cat_name] = {"total": 0.0, "color": cat_color}
        cat_totals[cat_name]["total"] += annualized

    # Top subscriptions by annual cost
    sub_items = []
    for sub in subscriptions:
        current_month = date.today().replace(day=1)
        proj = calculate_monthly_projection(sub, current_month)
        if proj is not None:
            annual = await exchange_rate_service.convert(db, proj * 12, sub.currency, preferred)
        else:
            annual = await exchange_rate_service.convert(db, sub.amount, sub.currency, preferred)
        cat = cat_map.get(sub.category_id) if sub.category_id else None
        sub_items.append({
            "id": sub.id,
            "name": sub.name,
            "annual_cost": round(annual, 2),
            "currency": preferred,
            "category_name": cat.name if cat else None,
            "category_color": cat.color if cat else None,
        })
    sub_items.sort(key=lambda x: x["annual_cost"], reverse=True)

    return AnnualReport(
        year=year,
        total=round(grand_total, 2),
        currency=preferred,
        monthly_totals=monthly_totals,
        category_totals=[{"name": k, "total": round(v["total"], 2), "color": v["color"]} for k, v in cat_totals.items()],
        top_subscriptions=sub_items[:10],
        subscription_count=len(subscriptions),
    )