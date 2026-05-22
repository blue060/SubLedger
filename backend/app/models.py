from datetime import date, datetime
from typing import Optional

from sqlalchemy import ForeignKey, Integer, String, Float, Boolean, Date, DateTime, Text, func, Table, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

subscription_tags = Table(
    "subscription_tags", Base.metadata,
    Column("subscription_id", Integer, ForeignKey("subscriptions.id"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id"), primary_key=True),
)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, default="admin")
    password_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    icon: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    color: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    subscriptions: Mapped[list["Subscription"]] = relationship("Subscription", back_populates="category")


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="CNY")
    billing_cycle: Mapped[str] = mapped_column(String(20), nullable=False)
    billing_cycle_num: Mapped[int] = mapped_column(Integer, default=1)
    billing_cycle_unit: Mapped[str] = mapped_column(String(10), default="month")
    first_payment_date: Mapped[date] = mapped_column(Date, nullable=False)
    next_payment_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    category_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("categories.id"), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    expiry_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    payment_method: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    intro_amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    intro_months: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    notify: Mapped[bool] = mapped_column(Boolean, default=True)
    auto_renew: Mapped[bool] = mapped_column(Boolean, default=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    shared_with: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    my_share: Mapped[float] = mapped_column(Float, default=100.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    category: Mapped[Optional["Category"]] = relationship("Category", back_populates="subscriptions", lazy="joined")
    notifications: Mapped[list["Notification"]] = relationship("Notification", back_populates="subscription", cascade="all, delete-orphan")
    price_history: Mapped[list["PriceHistory"]] = relationship("PriceHistory", cascade="all, delete-orphan")
    payment_records: Mapped[list["PaymentRecord"]] = relationship("PaymentRecord", back_populates="subscription", cascade="all, delete-orphan")
    tags: Mapped[list["Tag"]] = relationship("Tag", secondary=subscription_tags, back_populates="subscriptions")


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    subscription_id: Mapped[int] = mapped_column(Integer, ForeignKey("subscriptions.id"), nullable=False)
    message: Mapped[str] = mapped_column(String(500), nullable=False)
    notify_date: Mapped[date] = mapped_column(Date, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    sent_email: Mapped[bool] = mapped_column(Boolean, default=False)
    sent_push: Mapped[bool] = mapped_column(Boolean, default=False)
    sent_webhook: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    subscription: Mapped["Subscription"] = relationship("Subscription", back_populates="notifications")


class AppSettings(Base):
    __tablename__ = "app_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    preferred_currency: Mapped[str] = mapped_column(String(3), default="CNY")
    reminder_days: Mapped[int] = mapped_column(Integer, default=7)
    smtp_host: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    smtp_port: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    smtp_user: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    smtp_password: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    smtp_from: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    smtp_tls: Mapped[bool] = mapped_column(Boolean, default=True)
    bark_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    serverchan_key: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    exchange_rate_cache: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    exchange_rate_updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    monthly_budget: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    theme: Mapped[str] = mapped_column(String(10), default="light")
    webhook_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    wechat_webhook_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())


class PriceHistory(Base):
    __tablename__ = "price_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    subscription_id: Mapped[int] = mapped_column(Integer, ForeignKey("subscriptions.id"), nullable=False)
    old_amount: Mapped[float] = mapped_column(Float, nullable=False)
    new_amount: Mapped[float] = mapped_column(Float, nullable=False)
    old_currency: Mapped[str] = mapped_column(String(3), nullable=False)
    new_currency: Mapped[str] = mapped_column(String(3), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())


class PaymentRecord(Base):
    __tablename__ = "payment_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    subscription_id: Mapped[int] = mapped_column(Integer, ForeignKey("subscriptions.id"), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="CNY")
    payment_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    subscription: Mapped["Subscription"] = relationship("Subscription", back_populates="payment_records")


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    color: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    subscriptions: Mapped[list["Subscription"]] = relationship("Subscription", secondary=subscription_tags, back_populates="tags")


class BackupRecord(Base):
    __tablename__ = "backup_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())