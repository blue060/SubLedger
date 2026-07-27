import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ.setdefault("SECRET_KEY", "subledger-tests-only-secret-key-2026")

from datetime import date
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.security import hash_password
from app.models import User, Category, Subscription, Notification, AppSettings
from app.routers import auth, health, subscriptions, categories, dashboard, notifications, settings as settings_router, data, payments, tags, backups, search, analytics, users

TEST_DB_URL = "sqlite:///./test_subledger.db"
test_engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_test_app():
    """Create a test app without lifespan (no seed_database, no scheduler)."""
    app = FastAPI()
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
    app.dependency_overrides[get_db] = override_get_db
    return app


test_app = create_test_app()


@pytest.fixture
def db():
    Base.metadata.create_all(bind=test_engine)
    session = TestSessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=test_engine)
    test_engine.dispose()
    try:
        if os.path.exists("test_subledger.db"):
            os.remove("test_subledger.db")
    except PermissionError:
        pass


@pytest.fixture
def client(db):
    if db.query(User).count() == 0:
        db.add(User(username="admin", password_hash=hash_password("testpassword"), is_admin=True))
        db.commit()
    if db.query(AppSettings).count() == 0:
        admin_id = db.query(User.id).filter(User.username == "admin").scalar()
        db.add(AppSettings(user_id=admin_id, preferred_currency="CNY", reminder_days=7))
        db.commit()

    with TestClient(test_app) as c:
        yield c


@pytest.fixture
def auth_client(client):
    response = client.post("/api/auth/login", json={"password": "testpassword"})
    assert response.status_code == 200
    csrf_token = response.cookies.get("subledger_csrf")
    if csrf_token:
        client.headers["X-CSRF-Token"] = csrf_token
    return client


@pytest.fixture
def seed_categories(db):
    user_id = db.query(User.id).filter(User.username == "admin").scalar()
    cats = [
        Category(user_id=user_id, name="视频", icon="VideoPlay", color="#409EFF", sort_order=0),
        Category(user_id=user_id, name="音乐", icon="Headset", color="#67C23A", sort_order=1),
    ]
    for c in cats:
        db.add(c)
    db.commit()
    return db.query(Category).all()
