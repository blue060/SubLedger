from datetime import date, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from collections import defaultdict

from app.database import get_db
from app.dependencies import get_current_user
from app.models import Subscription, Category, AppSettings, PriceHistory
from app.schemas.advisor import AdvisorTip
from app.services.exchange_rate import exchange_rate_service
from app.services.billing import calculate_monthly_projection

router = APIRouter(prefix="/api/advisor", tags=["取消建议"], dependencies=[Depends(get_current_user)])


@router.get("/tips", response_model=list[AdvisorTip])
async def get_tips(db: Session = Depends(get_db)):
    settings = db.query(AppSettings).filter(AppSettings.id == 1).first()
    preferred = settings.preferred_currency if settings else "CNY"

    subscriptions = db.query(Subscription).filter(Subscription.is_active == True).all()
    categories = db.query(Category).all()
    cat_map = {c.id: c for c in categories}

    tips: list[AdvisorTip] = []
    today = date.today()
    current_month = today.replace(day=1)

    # 1. Price increases
    price_changes = db.query(PriceHistory).order_by(PriceHistory.created_at.desc()).all()
    seen_subs: set[int] = set()
    for ph in price_changes:
        if ph.subscription_id in seen_subs:
            continue
        sub = next((s for s in subscriptions if s.id == ph.subscription_id), None)
        if sub is None:
            continue
        seen_subs.add(ph.subscription_id)
        if ph.new_amount > ph.old_amount:
            diff = ph.new_amount - ph.old_amount
            converted_diff = await exchange_rate_service.convert(db, diff, sub.currency, preferred)
            tips.append(AdvisorTip(
                type="price_increase",
                subscription_id=sub.id,
                subscription_name=sub.name,
                message=f"{sub.name} 已从 {ph.old_currency} {ph.old_amount:.2f} 涨价至 {ph.new_currency} {ph.new_amount:.2f}",
                savings=round(converted_diff * 12, 2),
                currency=preferred,
            ))

    # 2. Duplicate services (same category, ≥2 active subs)
    by_category: dict[int, list] = defaultdict(list)
    for sub in subscriptions:
        if sub.category_id:
            by_category[sub.category_id].append(sub)

    for cat_id, subs in by_category.items():
        if len(subs) < 2:
            continue
        cat_name = cat_map[cat_id].name if cat_id in cat_map else "未分类"
        total_yearly = 0.0
        for sub in subs:
            proj = calculate_monthly_projection(sub, current_month)
            if proj is not None:
                yearly = proj * 12 if sub.billing_cycle != "yearly" else proj
                total_yearly += await exchange_rate_service.convert(db, yearly, sub.currency, preferred)

        tips.append(AdvisorTip(
            type="duplicate_service",
            subscription_id=subs[0].id,
            subscription_name=cat_name,
            message=f"「{cat_name}」分类下有 {len(subs)} 个订阅，考虑合并或取消其中一个",
            savings=round(total_yearly, 2),
            currency=preferred,
        ))

    # 3. Near expiry (next 7 days)
    near_expiry = [s for s in subscriptions if s.expiry_date and s.expiry_date <= today + timedelta(days=7)]
    for sub in near_expiry:
        remaining = (sub.expiry_date - today).days
        tips.append(AdvisorTip(
            type="near_expiry",
            subscription_id=sub.id,
            subscription_name=sub.name,
            message=f"{sub.name} 将在 {remaining} 天后到期，请决定是否续费",
        ))

    # 4. Top expensive subscriptions - cancel to save
    sub_yearly: list[tuple[Subscription, float]] = []
    for sub in subscriptions:
        proj = calculate_monthly_projection(sub, current_month)
        if proj is None:
            continue
        if sub.billing_cycle == "yearly":
            yearly = proj
        elif sub.billing_cycle == "quarterly":
            yearly = proj * 4
        else:
            yearly = proj * 12
        converted = await exchange_rate_service.convert(db, yearly, sub.currency, preferred)
        sub_yearly.append((sub, converted))

    sub_yearly.sort(key=lambda x: x[1], reverse=True)
    for sub, yearly_cost in sub_yearly[:3]:
        tips.append(AdvisorTip(
            type="cancel_to_save",
            subscription_id=sub.id,
            subscription_name=sub.name,
            message=f"取消 {sub.name} 每年可省 {preferred} {yearly_cost:.2f}",
            savings=round(yearly_cost, 2),
            currency=preferred,
        ))

    return tips