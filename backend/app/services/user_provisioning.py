from sqlalchemy.orm import Session

from app.models import AppSettings, Category


DEFAULT_CATEGORIES = [
    {"name": "视频", "icon": "VideoPlay", "color": "#409EFF", "sort_order": 0},
    {"name": "音乐", "icon": "Headset", "color": "#67C23A", "sort_order": 1},
    {"name": "云存储", "icon": "Cloudy", "color": "#E6A23C", "sort_order": 2},
    {"name": "会员", "icon": "User", "color": "#F56C6C", "sort_order": 3},
    {"name": "游戏", "icon": "GamePad", "color": "#C0C4FC", "sort_order": 4},
    {"name": "AI工具", "icon": "MagicStick", "color": "#9B59B6", "sort_order": 5},
    {"name": "云服务", "icon": "Cloudy", "color": "#3498DB", "sort_order": 6},
    {"name": "域名", "icon": "Connection", "color": "#14B8A6", "sort_order": 7},
    {"name": "其他", "icon": "More", "color": "#DCDFE6", "sort_order": 8},
]


def ensure_user_workspace(
    db: Session,
    user_id: int,
    preferred_currency: str = "CNY",
    reminder_days: int = 7,
) -> None:
    if not db.query(Category.id).filter(Category.user_id == user_id).first():
        db.add_all([Category(user_id=user_id, **category) for category in DEFAULT_CATEGORIES])
    if not db.query(AppSettings.id).filter(AppSettings.user_id == user_id).first():
        db.add(AppSettings(
            user_id=user_id,
            preferred_currency=preferred_currency,
            reminder_days=reminder_days,
        ))
