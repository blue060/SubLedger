from contextlib import asynccontextmanager
import logging
import os

from fastapi import FastAPI
from starlette.responses import FileResponse
from sqlalchemy import text

from app.config import get_settings
from app.database import Base, engine, SessionLocal
from app.models import User, Category, Notification, Subscription, AppSettings, PaymentRecord, Tag, BackupRecord
from app.routers import auth, health, subscriptions, categories, dashboard, notifications, settings as settings_router, data, payments, tags, backups, search, analytics, users
from app.services.scheduler import start_scheduler, stop_scheduler
from app.services.payment_sync import sync_due_payments
from app.services.admin_bootstrap import ensure_initial_admin, load_or_create_runtime_secret
from app.services.subscription_lifecycle import deactivate_expired_subscriptions
from app.services.user_provisioning import ensure_user_workspace
from app.middleware.csrf import CSRFMiddleware
from app.middleware.rate_limit import RateLimitMiddleware

logger = logging.getLogger("subledger")

# New columns added in recent versions that need auto-migration for existing SQLite DBs
MIGRATIONS = [
    ("users", "is_admin", "BOOLEAN DEFAULT 0 NOT NULL"),
    ("categories", "user_id", "INTEGER REFERENCES users(id)"),
    ("subscriptions", "user_id", "INTEGER REFERENCES users(id)"),
    ("app_settings", "user_id", "INTEGER REFERENCES users(id)"),
    ("tags", "user_id", "INTEGER REFERENCES users(id)"),
    ("backup_records", "user_id", "INTEGER REFERENCES users(id)"),
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
        conn.execute(text(
            "CREATE INDEX IF NOT EXISTS ix_subscriptions_user_active "
            "ON subscriptions (user_id, is_active)"
        ))
        conn.execute(text(
            "CREATE INDEX IF NOT EXISTS ix_categories_user_sort "
            "ON categories (user_id, sort_order)"
        ))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_tags_user_id ON tags (user_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_backup_records_user_id ON backup_records (user_id)"))
        conn.commit()


def migrate_user_ownership():
    """Assign all legacy single-user data to the original administrator."""
    db = SessionLocal()
    try:
        first_user = db.query(User).order_by(User.id).first()
        if not first_user:
            return
        if not db.query(User.id).filter(User.is_admin == True).first():
            first_user.is_admin = True

        for model in (Category, Subscription, AppSettings, Tag, BackupRecord):
            db.query(model).filter(model.user_id == None).update(
                {model.user_id: first_user.id}, synchronize_session=False
            )
        db.commit()
        with engine.connect() as conn:
            conn.execute(text(
                "CREATE UNIQUE INDEX IF NOT EXISTS uq_app_settings_user_id "
                "ON app_settings (user_id)"
            ))
            conn.commit()
    finally:
        db.close()


def migrate_tag_uniqueness():
    """Replace the legacy global tag-name constraint with a per-user one."""
    with engine.connect() as conn:
        indexes = conn.execute(text("PRAGMA index_list(tags)")).fetchall()
        has_global_unique_name = False
        for index in indexes:
            if not index[2]:
                continue
            columns = conn.execute(text(f"PRAGMA index_info('{index[1]}')")).fetchall()
            if [column[2] for column in columns] == ["name"]:
                has_global_unique_name = True
                break
    if not has_global_unique_name:
        return

    connection = engine.raw_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("PRAGMA foreign_keys=OFF")
        cursor.execute("BEGIN")
        cursor.execute(
            "CREATE TEMP TABLE subscription_tags_backup AS "
            "SELECT subscription_id, tag_id FROM subscription_tags"
        )
        cursor.execute("DROP TABLE subscription_tags")
        cursor.execute(
            "CREATE TABLE tags_new ("
            "id INTEGER NOT NULL PRIMARY KEY, user_id INTEGER NOT NULL, "
            "name VARCHAR(50) NOT NULL, color VARCHAR(7), created_at DATETIME, "
            "CONSTRAINT uq_tags_user_name UNIQUE (user_id, name), "
            "FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE)"
        )
        cursor.execute(
            "INSERT INTO tags_new (id, user_id, name, color, created_at) "
            "SELECT id, user_id, name, color, created_at FROM tags"
        )
        cursor.execute("DROP TABLE tags")
        cursor.execute("ALTER TABLE tags_new RENAME TO tags")
        cursor.execute("CREATE INDEX ix_tags_user_id ON tags (user_id)")
        cursor.execute(
            "CREATE TABLE subscription_tags ("
            "subscription_id INTEGER NOT NULL, tag_id INTEGER NOT NULL, "
            "PRIMARY KEY (subscription_id, tag_id), "
            "FOREIGN KEY(subscription_id) REFERENCES subscriptions(id) ON DELETE CASCADE, "
            "FOREIGN KEY(tag_id) REFERENCES tags(id) ON DELETE CASCADE)"
        )
        cursor.execute(
            "INSERT INTO subscription_tags (subscription_id, tag_id) "
            "SELECT subscription_id, tag_id FROM subscription_tags_backup"
        )
        cursor.execute("DROP TABLE subscription_tags_backup")
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
        connection.close()


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

        for user_id, in db.query(User.id).all():
            ensure_user_workspace(
                db,
                user_id,
                preferred_currency=settings.DEFAULT_CURRENCY,
                reminder_days=settings.REMINDER_DAYS,
            )
        db.commit()
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
        migrated_deprecated = False
        for user_id, in db.query(User.id).all():
            other = db.query(Category).filter(
                Category.user_id == user_id, Category.name == "其他"
            ).order_by(Category.id).first()
            if not other:
                other = Category(user_id=user_id, name="其他", icon="More", color="#DCDFE6", sort_order=999)
                db.add(other)
                db.flush()

            deprecated = db.query(Category).filter(
                Category.user_id == user_id,
                Category.name.in_(["工具", "开发工具"]),
            ).all()
            for category in deprecated:
                db.query(Subscription).filter(
                    Subscription.user_id == user_id,
                    Subscription.category_id == category.id,
                ).update({Subscription.category_id: other.id}, synchronize_session=False)
                db.delete(category)
                migrated_deprecated = True

            domain = db.query(Category).filter(
                Category.user_id == user_id, Category.name == "域名"
            ).order_by(Category.id).first()
            if not domain:
                current_max = max((row[0] or 0 for row in db.query(Category.sort_order).filter(Category.user_id == user_id).all()), default=0)
                db.add(Category(user_id=user_id, name="域名", icon="Connection", color="#14B8A6", sort_order=current_max + 1))

            max_order = max((row[0] or 0 for row in db.query(Category.sort_order).filter(
                Category.user_id == user_id, Category.id != other.id
            ).all()), default=0)
            other.sort_order = max_order + 1
        db.commit()
        if migrated_deprecated:
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
    migrate_database()
    initialize_admin_user()
    migrate_user_ownership()
    migrate_tag_uniqueness()
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
app.include_router(users.router)

# Static files & SPA fallback
static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "static")


@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    file_path = os.path.join(static_dir, full_path)
    if full_path and os.path.isfile(file_path):
        return FileResponse(file_path)
    return FileResponse(os.path.join(static_dir, "index.html"))
