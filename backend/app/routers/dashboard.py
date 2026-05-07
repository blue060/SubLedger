from dateutil.relativedelta import relativedelta
from datetime import date, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import Subscription, AppSettings, Category
from app.schemas.dashboard import DashboardSummary, CategoryStat, CalendarEntry, ExpiringSubscription, MonthlyTrend, BudgetStatus
from app.services.exchange_rate import exchange_rate_service
from app.services.billing import calculate_monthly_projection, _effective_amount

router = APIRouter(prefix="/api/dashboard", tags=["仪表盘"], dependencies=[Depends(get_current_user)])


@router.get("/summary", response_model=DashboardSummary)
async def get_summary(db: Session = Depends(get_db)):
    settings = db.query(AppSettings).filter(AppSettings.id == 1).first()
    preferred = settings.preferred_currency if settings else "CNY"

    today = date.today()
    current_month = today.replace(day=1)
    next_month = (current_month + timedelta(days=32)).replace(day=1)
    last_month = current_month - relativedelta(months=1)

    subscriptions = db.query(Subscription).filter(Subscription.is_active == True).all()

    # Collect amounts by currency to batch conversions
    current_by_cur: dict[str, float] = {}
    next_by_cur: dict[str, float] = {}
    last_by_cur: dict[str, float] = {}
    yearly_by_cur: dict[str, float] = {}

    for sub in subscriptions:
        proj_current = calculate_monthly_projection(sub, current_month)
        if proj_current is not None:
            current_by_cur[sub.currency] = current_by_cur.get(sub.currency, 0) + proj_current

        proj_next = calculate_monthly_projection(sub, next_month)
        if proj_next is not None:
            next_by_cur[sub.currency] = next_by_cur.get(sub.currency, 0) + proj_next

        proj_last = calculate_monthly_projection(sub, last_month)
        if proj_last is not None:
            last_by_cur[sub.currency] = last_by_cur.get(sub.currency, 0) + proj_last

        for i in range(12):
            m = current_month + relativedelta(months=i)
            proj = calculate_monthly_projection(sub, m)
            if proj is not None:
                yearly_by_cur[sub.currency] = yearly_by_cur.get(sub.currency, 0) + proj

    # One conversion per currency per period
    async def sum_converted(amounts_by_cur: dict[str, float]) -> float:
        total = 0.0
        for cur, amount in amounts_by_cur.items():
            total += await exchange_rate_service.convert(db, amount, cur, preferred)
        return total

    monthly_total = await sum_converted(current_by_cur)
    next_month_total = await sum_converted(next_by_cur)
    last_month_total = await sum_converted(last_by_cur)
    yearly_total = await sum_converted(yearly_by_cur)

    monthly_change = round(monthly_total - last_month_total, 2)

    return DashboardSummary(
        monthly_total=round(monthly_total, 2),
        monthly_total_currency=preferred,
        next_month_projected=round(next_month_total, 2),
        next_month_projected_currency=preferred,
        yearly_total=round(yearly_total, 2),
        yearly_total_currency=preferred,
        last_month_total=round(last_month_total, 2),
        last_month_total_currency=preferred,
        monthly_change=monthly_change,
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
async def get_calendar(
    year: Optional[int] = Query(default=None, ge=2000, le=2100),
    month: Optional[int] = Query(default=None, ge=1, le=12),
    db: Session = Depends(get_db),
):
    settings = db.query(AppSettings).filter(AppSettings.id == 1).first()
    preferred = settings.preferred_currency if settings else "CNY"

    today = date.today()
    if year and month:
        start_date = date(year, month, 1)
        end_date = (start_date + relativedelta(months=1)) - timedelta(days=1)
    else:
        start_date = today
        end_date = today + timedelta(days=30)

    subscriptions = db.query(Subscription).filter(Subscription.is_active == True).all()
    categories = db.query(Category).all()
    cat_map = {c.id: c for c in categories}

    entries = []
    for sub in subscriptions:
        if sub.expiry_date and sub.expiry_date < start_date:
            continue

        cat_color = cat_map[sub.category_id].color if sub.category_id and sub.category_id in cat_map else None

        if sub.billing_cycle in ("once", "permanent"):
            pd = sub.first_payment_date
            if pd < start_date or pd > end_date:
                continue
            effective = _effective_amount(sub, pd, start_date.replace(day=1))
            converted = await exchange_rate_service.convert(db, effective, sub.currency, preferred)
            entries.append(CalendarEntry(
                date=pd,
                subscription_id=sub.id,
                subscription_name=sub.name,
                amount=effective,
                currency=sub.currency,
                converted_amount=round(converted, 2),
                category_color=cat_color,
            ))
            continue

        if sub.next_payment_date is None or sub.next_payment_date < start_date or sub.next_payment_date > end_date:
            continue
        effective = _effective_amount(sub, sub.next_payment_date, start_date.replace(day=1))
        converted = await exchange_rate_service.convert(db, effective, sub.currency, preferred)
        entries.append(CalendarEntry(
            date=sub.next_payment_date,
            subscription_id=sub.id,
            subscription_name=sub.name,
            amount=effective,
            currency=sub.currency,
            converted_amount=round(converted, 2),
            category_color=cat_color,
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