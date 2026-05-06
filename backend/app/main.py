from contextlib import asynccontextmanager
import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import FileResponse
from sqlalchemy import text

from app.config import get_settings
from app.database import Base, engine, SessionLocal
from app.models import User, Category, Notification, Subscription, AppSettings
from app.routers import auth, health, subscriptions, categories, dashboard, notifications, settings as settings_router, data
from app.services.scheduler import start_scheduler, stop_scheduler

logger = logging.getLogger("subledger")

# New columns added in recent versions that need auto-migration for existing SQLite DBs
MIGRATIONS = [
    ("subscriptions", "billing_cycle_num", "INTEGER DEFAULT 1 NOT NULL"),
    ("subscriptions", "billing_cycle_unit", "VARCHAR(10) DEFAULT 'month' NOT NULL"),
    ("subscriptions", "intro_amount", "FLOAT"),
    ("subscriptions", "intro_months", "INTEGER"),
    ("subscriptions", "url", "VARCHAR(500)"),
    ("subscriptions", "expiry_date", "DATE"),
    ("subscriptions", "payment_method", "VARCHAR(100)"),
    ("app_settings", "monthly_budget", "FLOAT"),
    ("app_settings", "theme", "VARCHAR(10) DEFAULT 'light' NOT NULL"),
]

DEFAULT_CATEGORIES = [
    {"name": "视频", "icon": "VideoPlay", "color": "#409EFF", "sort_order": 0},
    {"name": "音乐", "icon": "Headset", "color": "#67C23A", "sort_order": 1},
    {"name": "云存储", "icon": "Cloudy", "color": "#E6A23C", "sort_order": 2},
    {"name": "会员", "icon": "User", "color": "#F56C6C", "sort_order": 3},
    {"name": "工具", "icon": "Setting", "color": "#909399", "sort_order": 4},
    {"name": "游戏", "icon": "GamePad", "color": "#C0C4FC", "sort_order": 5},
    {"name": "其他", "icon": "More", "color": "#DCDFE6", "sort_order": 6},
    {"name": "AI工具", "icon": "MagicStick", "color": "#9B59B6", "sort_order": 7},
    {"name": "开发工具", "icon": "Cpu", "color": "#1ABC9C", "sort_order": 8},
    {"name": "云服务", "icon": "Cloudy", "color": "#3498DB", "sort_order": 9},
]


def migrate_database():
    with engine.connect() as conn:
        for table, column, col_type in MIGRATIONS:
            existing = {row[1] for row in conn.execute(text(f"PRAGMA table_info({table})"))}
            if column not in existing:
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}"))
                logger.info(f"自动迁移: {table}.{column} 已添加")
        conn.commit()


def seed_database():
    db = SessionLocal()
    try:
        settings = get_settings()

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
    migrate_database()
    seed_database()
    start_scheduler()
    logger.info("SubLedger 启动完成")
    yield
    stop_scheduler()
    logger.info("SubLedger 关闭")


app = FastAPI(title="SubLedger", lifespan=lifespan, docs_url=None, redoc_url=None)

# Middleware (order: last added = first executed)
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

# Static files & SPA fallback
static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "static")


@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    file_path = os.path.join(static_dir, full_path)
    if full_path and os.path.isfile(file_path):
        return FileResponse(file_path)
    return FileResponse(os.path.join(static_dir, "index.html"))