from contextlib import asynccontextmanager
import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.database import Base, engine, SessionLocal
from app.models import User, Category, Notification, Subscription, AppSettings
from app.middleware.rate_limit import RateLimitMiddleware
from app.routers import auth, health, subscriptions, categories, dashboard, notifications, settings as settings_router, data
from app.services.scheduler import start_scheduler, stop_scheduler

logger = logging.getLogger("subledger")

DEFAULT_CATEGORIES = [
    {"name": "视频", "icon": "VideoPlay", "color": "#409EFF", "sort_order": 0},
    {"name": "音乐", "icon": "Headset", "color": "#67C23A", "sort_order": 1},
    {"name": "云存储", "icon": "Cloudy", "color": "#E6A23C", "sort_order": 2},
    {"name": "会员", "icon": "User", "color": "#F56C6C", "sort_order": 3},
    {"name": "工具", "icon": "Setting", "color": "#909399", "sort_order": 4},
    {"name": "游戏", "icon": "GamePad", "color": "#C0C4FC", "sort_order": 5},
    {"name": "其他", "icon": "More", "color": "#DCDFE6", "sort_order": 6},
]


def seed_database():
    from app.security import hash_password

    db = SessionLocal()
    try:
        settings = get_settings()
        if not settings.ADMIN_PASSWORD:
            logger.error("ADMIN_PASSWORD 环境变量未设置，应用无法启动")
            raise SystemExit(1)

        # Seed admin user
        if db.query(User).count() == 0:
            db.add(User(username="admin", password_hash=hash_password(settings.ADMIN_PASSWORD)))
            db.commit()
            logger.info("已创建管理员账户")

        # Seed default categories
        if db.query(Category).count() == 0:
            for cat in DEFAULT_CATEGORIES:
                db.add(Category(**cat))
            db.commit()
            logger.info("已创建默认分类")

        # Seed app settings
        if db.query(AppSettings).count() == 0:
            db.add(AppSettings(
                preferred_currency=settings.DEFAULT_CURRENCY,
                reminder_days=settings.REMINDER_DAYS,
            ))
            db.commit()
            logger.info("已初始化应用设置")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    Base.metadata.create_all(bind=engine)
    seed_database()
    start_scheduler()
    logger.info("SubLedger 启动完成")
    yield
    stop_scheduler()
    logger.info("SubLedger 关闭")


app = FastAPI(title="SubLedger", lifespan=lifespan, docs_url=None, redoc_url=None)

# Middleware (order: last added = first executed)
app.add_middleware(RateLimitMiddleware, max_requests=60, window_seconds=60)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router)
app.include_router(health.router)
app.include_router(subscriptions.router)
app.include_router(categories.router)
app.include_router(dashboard.router)
app.include_router(notifications.router)
app.include_router(settings_router.router)
app.include_router(data.router)

# Static files (Vue build output)
static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "static")
if os.path.isdir(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")