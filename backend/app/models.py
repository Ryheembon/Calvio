from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    business_name: Mapped[str] = mapped_column(String(120))
    slug: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    bio: Mapped[str] = mapped_column(Text, default="")
    slot_minutes: Mapped[int] = mapped_column(Integer, default=30)
    stripe_customer_id: Mapped[str | None] = mapped_column(String(255), nullable=True, default=None)
    stripe_subscription_id: Mapped[str | None] = mapped_column(String(255), nullable=True, default=None)
    plan_status: Mapped[str] = mapped_column(String(32), default="free")  # free | active | past_due | canceled
    reset_token_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, default=None)
    reset_token_expires: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    availability = relationship("Availability", back_populates="user", cascade="all, delete-orphan")
    appointments = relationship("Appointment", back_populates="user", cascade="all, delete-orphan")

    @property
    def is_pro(self) -> bool:
        return (self.plan_status or "free") == "active"


class Availability(Base):
    __tablename__ = "availability"
    __table_args__ = (UniqueConstraint("user_id", "day_of_week", name="uq_user_day"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    day_of_week: Mapped[int] = mapped_column(Integer)  # 0=Monday ... 6=Sunday
    start_minute: Mapped[int] = mapped_column(Integer, default=9 * 60)  # minutes from midnight
    end_minute: Mapped[int] = mapped_column(Integer, default=17 * 60)
    is_open: Mapped[bool] = mapped_column(Boolean, default=True)

    user = relationship("User", back_populates="availability")


class Appointment(Base):
    __tablename__ = "appointments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    client_name: Mapped[str] = mapped_column(String(120))
    client_email: Mapped[str] = mapped_column(String(255))
    starts_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    ends_at: Mapped[datetime] = mapped_column(DateTime)
    notes: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(20), default="confirmed")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="appointments")
