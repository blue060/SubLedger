import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datetime import date
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.security import hash_password
from app.models import User, Category, Subscription, Notification, AppSettings
from app.routers import auth, health, subscriptions, categories, dashboard, notifications, settings as settings_router, data

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
    try:
        if os.path.exists("test_subledger.db"):
            os.remove("test_subledger.db")
    except PermissionError:
        pass


@pytest.fixture
def client(db):
    if db.query(User).count() == 0:
        db.add(User(username="admin", password_hash=hash_password("testpassword")))
        db.commit()
    if db.query(AppSettings).count() == 0:
        db.add(AppSettings(preferred_currency="CNY", reminder_days=7))
        db.commit()

    with TestClient(test_app) as c:
        yield c


@pytest.fixture
def auth_client(client):
    response = client.post("/api/auth/login", json={"password": "testpassword"})
    assert response.status_code == 200
    return client


@pytest.fixture
def seed_categories(db):
    cats = [
        Category(name="视频", icon="VideoPlay", color="#409EFF", sort_order=0),
        Category(name="音乐", icon="Headset", color="#67C23A", sort_order=1),
    ]
    for c in cats:
        db.add(c)
    db.commit()
    return db.query(Category).all()