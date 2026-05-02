from datetime import date, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import Subscription, AppSettings, Category
from app.schemas.dashboard import DashboardSummary, CategoryStat, CalendarEntry, ExpiringSubscription, MonthlyTrend, BudgetStatus
from app.services.exchange_rate import exchange_rate_service
from app.services.billing import calculate_monthly_projection

router = APIRouter(prefix="/api/dashboard", tags=["仪表盘"], dependencies=[Depends(get_current_user)])


@router.get("/summary", response_model=DashboardSummary)
async def get_summary(db: Session = Depends(get_db)):
    settings = db.query(AppSettings).filter(AppSettings.id == 1).first()
    preferred = settings.preferred_currency if settings else "CNY"

    today = date.today()
    current_month = today.replace(day=1)
    next_month = (current_month + timedelta(days=32)).replace(day=1)

    subscriptions = db.query(Subscription).filter(Subscription.is_active == True).all()

    monthly_total = 0.0
    next_month_total = 0.0

    for sub in subscriptions:
        proj_current = calculate_monthly_projection(sub, current_month)
        if proj_current is not None:
            converted = await exchange_rate_service.convert(db, proj_current, sub.currency, preferred)
            monthly_total += converted

        proj_next = calculate_monthly_projection(sub, next_month)
        if proj_next is not None:
            converted = await exchange_rate_service.convert(db, proj_next, sub.currency, preferred)
            next_month_total += converted

    return DashboardSummary(
        monthly_total=round(monthly_total, 2),
        monthly_total_currency=preferred,
        next_month_projected=round(next_month_total, 2),
        next_month_projected_currency=preferred,
    )


@router.get("/stats", response_model=list[CategoryStat])
async def get_stats(db: Session = Depends(get_db)):
    settings = db.query(AppSettings).filter(AppSettings.id == 1).first()
    preferred = settings.preferred_currency if settings else "CNY"

    today = date.today()
    current_month = today.replace(day=1)
    subscriptions = db.query(Subscription).filter(Subscription.is_active == True).all()
    categories = db.query(Category).all()
    cat_map = {c.id: c for c in categories}

    stats: dict[str, CategoryStat] = {}

    for sub in subscriptions:
        proj = calculate_monthly_projection(sub, current_month)
        if proj is None:
            continue
        converted = await exchange_rate_service.convert(db, proj, sub.currency, preferred)
        cat_name = cat_map[sub.category_id].name if sub.category_id and sub.category_id in cat_map else "未分类"
        cat_color = cat_map[sub.category_id].color if sub.category_id and sub.category_id in cat_map else "#909399"

        if cat_name not in stats:
            stats[cat_name] = CategoryStat(category_name=cat_name, color=cat_color, total_amount=0.0)
        stats[cat_name].total_amount += converted

    for s in stats.values():
        s.total_amount = round(s.total_amount, 2)

    return list(stats.values())


@router.get("/calendar", response_model=list[CalendarEntry])
async def get_calendar(db: Session = Depends(get_db)):
    settings = db.query(AppSettings).filter(AppSettings.id == 1).first()
    preferred = settings.preferred_currency if settings else "CNY"

    today = date.today()
    end_date = today + timedelta(days=30)
    subscriptions = db.query(Subscription).filter(Subscription.is_active == True).all()

    entries = []
    for sub in subscriptions:
        if sub.next_payment_date < today or sub.next_payment_date > end_date:
            continue
        converted = await exchange_rate_service.convert(db, sub.amount, sub.currency, preferred)
        entries.append(CalendarEntry(
            date=sub.next_payment_date,
            subscription_name=sub.name,
            amount=sub.amount,
            currency=sub.currency,
            converted_amount=round(converted, 2),
        ))

    entries.sort(key=lambda e: e.date)
    return entries


@router.get("/expiring", response_model=list[ExpiringSubscription])
def get_expiring(days: int = Query(default=30, ge=1, le=365), db: Session = Depends(get_db)):
    today = date.today()
    threshold = today + timedelta(days=days)
    subs = db.query(Subscription).filter(
        Subscription.is_active == True,
        Subscription.expiry_date != None,
        Subscription.expiry_date <= threshold,
    ).order_by(Subscription.expiry_date).all()

    result = []
    for sub in subs:
        result.append(ExpiringSubscription(
            id=sub.id,
            name=sub.name,
            expiry_date=sub.expiry_date,
            remaining_days=(sub.expiry_date - today).days,
        ))
    return result


@router.get("/trend", response_model=list[MonthlyTrend])
async def get_trend(months: int = Query(default=12, ge=1, le=24), db: Session = Depends(get_db)):
    settings = db.query(AppSettings).filter(AppSettings.id == 1).first()
    preferred = settings.preferred_currency if settings else "CNY"
    subscriptions = db.query(Subscription).filter(Subscription.is_active == True).all()

    today = date.today()
    result = []
    for i in range(months - 1, -1, -1):
        target = (today.replace(day=1) - timedelta(days=1) * 30 * i)
        target = (today.replace(day=1) - timedelta(days=i * 30)).replace(day=1)
        # Correct month calculation
        m = today.month - i
        y = today.year
        while m <= 0:
            m += 12
            y -= 1
        target = date(y, m, 1)

        total = 0.0
        for sub in subscriptions:
            proj = calculate_monthly_projection(sub, target)
            if proj is not None:
                converted = await exchange_rate_service.convert(db, proj, sub.currency, preferred)
                total += converted
        result.append(MonthlyTrend(month=target.strftime("%Y-%m"), total=round(total, 2)))

    return result


@router.get("/budget", response_model=BudgetStatus)
async def get_budget(db: Session = Depends(get_db)):
    settings = db.query(AppSettings).filter(AppSettings.id == 1).first()
    preferred = settings.preferred_currency if settings else "CNY"
    budget = settings.monthly_budget if settings else None

    today = date.today()
    current_month = today.replace(day=1)
    subscriptions = db.query(Subscription).filter(Subscription.is_active == True).all()

    spent = 0.0
    for sub in subscriptions:
        proj = calculate_monthly_projection(sub, current_month)
        if proj is not None:
            converted = await exchange_rate_service.convert(db, proj, sub.currency, preferred)
            spent += converted

    spent = round(spent, 2)
    remaining = round(budget - spent, 2) if budget else None

    return BudgetStatus(
        budget=budget,
        spent=spent,
        remaining=remaining,
        exceeded=budget is not None and spent > budget,
    )