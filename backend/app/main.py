from contextlib import asynccontextmanager
import logging
import os

from fastapi import FastAPI
from starlette.responses import FileResponse
from sqlalchemy import text

from app.config import get_settings
from app.database import Base, engine, SessionLocal
from app.models import User, Category, Notification, Subscription, AppSettings, PaymentRecord, Tag, BackupRecord
from app.routers import auth, health, subscriptions, categories, dashboard, notifications, settings as settings_router, data, payments, tags, backups, search, analytics
from app.services.scheduler import start_scheduler, stop_scheduler
from app.services.payment_sync import sync_due_payments
from app.services.admin_bootstrap import ensure_initial_admin, load_or_create_runtime_secret
from app.services.subscription_lifecycle import deactivate_expired_subscriptions
from app.middleware.csrf import CSRFMiddleware
from app.middleware.rate_limit import RateLimitMiddleware

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
    ("subscriptions", "shared_with", "VARCHAR(200)"),
    ("subscriptions", "my_share", "FLOAT DEFAULT 100.0 NOT NULL"),
    ("app_settings", "webhook_url", "VARCHAR(500)"),
    ("notifications", "sent_webhook", "BOOLEAN DEFAULT 0 NOT NULL"),
    ("subscriptions", "auto_renew", "BOOLEAN DEFAULT 1 NOT NULL"),
    ("app_settings", "wechat_webhook_url", "VARCHAR(500)"),
]

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


def migrate_database():
    with engine.connect() as conn:
        for table, column, col_type in MIGRATIONS:
            existing = {row[1] for row in conn.execute(text(f"PRAGMA table_info({table})"))}
            if column not in existing:
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}"))
                logger.info(f"自动迁移: {table}.{column} 已添加")
        conn.execute(text(
            "CREATE INDEX IF NOT EXISTS ix_payment_records_subscription_date "
            "ON payment_records (subscription_id, payment_date)"
        ))
        conn.execute(text(
            "CREATE INDEX IF NOT EXISTS ix_payment_records_status_date "
            "ON payment_records (status, payment_date)"
        ))
        conn.execute(text(
            "CREATE INDEX IF NOT EXISTS ix_subscriptions_billing_sync "
            "ON subscriptions (is_active, auto_renew, billing_cycle, next_payment_date)"
        ))
        conn.commit()


def migrate_auto_renew():
    with engine.connect() as conn:
        result = conn.execute(text(
            "UPDATE subscriptions SET auto_renew = 0 "
            "WHERE billing_cycle IN ('once', 'permanent') AND auto_renew = 1"
        ))
        if result.rowcount > 0:
            logger.info(f"自动迁移: 将 {result.rowcount} 个一次性/永久订阅设置为 auto_renew=False")
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


def initialize_admin_user():
    db = SessionLocal()
    try:
        settings = get_settings()
        settings.SECRET_KEY = load_or_create_runtime_secret(
            settings.SECRET_KEY,
            settings.ENV,
            settings.SECRET_KEY_FILE,
        )
        if ensure_initial_admin(db, settings.ADMIN_USERNAME, settings.ADMIN_PASSWORD):
            logger.info("已通过服务器环境变量创建初始管理员")
    finally:
        db.close()


def migrate_categories():
    """Apply the revised built-in category set without losing subscriptions."""
    db = SessionLocal()
    try:
        other = db.query(Category).filter(Category.name == "其他").order_by(Category.id).first()
        if not other:
            other = Category(name="其他", icon="More", color="#DCDFE6", sort_order=999)
            db.add(other)
            db.flush()

        deprecated = db.query(Category).filter(Category.name.in_(["工具", "开发工具"])).all()
        for category in deprecated:
            db.query(Subscription).filter(Subscription.category_id == category.id).update(
                {Subscription.category_id: other.id}, synchronize_session=False
            )
            db.delete(category)

        domain = db.query(Category).filter(Category.name == "域名").order_by(Category.id).first()
        if not domain:
            current_max = max((row[0] or 0 for row in db.query(Category.sort_order).all()), default=0)
            domain = Category(name="域名", icon="Connection", color="#14B8A6", sort_order=current_max + 1)
            db.add(domain)
            db.flush()

        max_order = max((row[0] or 0 for row in db.query(Category.sort_order).filter(Category.id != other.id).all()), default=0)
        other.sort_order = max_order + 1
        db.commit()
        if deprecated:
            logger.info("分类迁移完成: 已移除工具/开发工具并将其订阅归入其他")
    finally:
        db.close()


def sync_payments_on_startup():
    db = SessionLocal()
    try:
        disabled = deactivate_expired_subscriptions(db)
        if disabled:
            logger.info(f"启动检查: 已自动停用 {disabled} 个过期订阅")
        sync_due_payments(db)
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    Base.metadata.create_all(bind=engine)
    initialize_admin_user()
    migrate_database()
    migrate_auto_renew()
    seed_database()
    migrate_categories()
    sync_payments_on_startup()
    start_scheduler()
    logger.info("SubLedger 启动完成")
    yield
    stop_scheduler()
    logger.info("SubLedger 关闭")


app = FastAPI(title="SubLedger", lifespan=lifespan, docs_url=None, redoc_url=None)

# Middleware (order: last added = first executed)
app.add_middleware(CSRFMiddleware)
app.add_middleware(RateLimitMiddleware)

# Routers
app.include_router(auth.router)
app.include_router(health.router)
app.include_router(subscriptions.router)
app.include_router(categories.router)
app.include_router(dashboard.router)
app.include_router(notifications.router)
app.include_router(settings_router.router)
app.include_router(data.router)
app.include_router(payments.router)
app.include_router(tags.router)
app.include_router(backups.router)
app.include_router(search.router)
app.include_router(analytics.router)

# Static files & SPA fallback
static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "static")


@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    file_path = os.path.join(static_dir, full_path)
    if full_path and os.path.isfile(file_path):
        return FileResponse(file_path)
    return FileResponse(os.path.join(static_dir, "index.html"))
