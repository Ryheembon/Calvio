import stripe
from fastapi import HTTPException
from sqlalchemy.orm import Session

from .config import settings
from .models import User


def stripe_ready() -> bool:
    return bool(settings.stripe_secret_key and settings.stripe_price_id)


def require_stripe() -> None:
    if not stripe_ready():
        raise HTTPException(
            status_code=503,
            detail="Stripe is not configured yet. Add STRIPE_SECRET_KEY and STRIPE_PRICE_ID.",
        )
    stripe.api_key = settings.stripe_secret_key


def stripe_error(exc: Exception) -> HTTPException:
    message = getattr(exc, "user_message", None) or str(exc)
    return HTTPException(status_code=400, detail=f"Stripe error: {message}")


def plan_from_subscription_status(status: str | None) -> str:
    if status in ("active", "trialing"):
        return "active"
    if status == "past_due":
        return "past_due"
    if status in ("canceled", "unpaid", "incomplete_expired"):
        return "canceled"
    return "free"


def ensure_customer(db: Session, user: User) -> str:
    require_stripe()
    if user.stripe_customer_id:
        return user.stripe_customer_id

    customer = stripe.Customer.create(
        email=user.email,
        name=user.business_name,
        metadata={"user_id": str(user.id), "slug": user.slug},
    )
    user.stripe_customer_id = customer.id
    db.commit()
    db.refresh(user)
    return customer.id


def apply_subscription(db: Session, user: User, subscription) -> None:
    user.stripe_subscription_id = subscription.id
    user.plan_status = plan_from_subscription_status(getattr(subscription, "status", None))
    customer_id = getattr(subscription, "customer", None)
    if customer_id and not user.stripe_customer_id:
        user.stripe_customer_id = customer_id
    db.commit()


def find_user_for_subscription(db: Session, subscription) -> User | None:
    metadata = getattr(subscription, "metadata", None) or {}
    user_id = metadata.get("user_id") if hasattr(metadata, "get") else None
    if user_id:
        user = db.query(User).filter(User.id == int(user_id)).first()
        if user:
            return user

    sub_id = getattr(subscription, "id", None)
    if sub_id:
        user = db.query(User).filter(User.stripe_subscription_id == sub_id).first()
        if user:
            return user

    customer_id = getattr(subscription, "customer", None)
    if customer_id:
        return db.query(User).filter(User.stripe_customer_id == customer_id).first()
    return None
