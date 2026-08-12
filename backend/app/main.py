from datetime import date, datetime, timedelta

import stripe
from fastapi import Depends, FastAPI, HTTPException, Query, Request, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .auth import (
    create_access_token,
    create_password_reset_token,
    get_current_user,
    hash_password,
    hash_reset_token,
    slugify,
    verify_password,
)
from .billing import (
    apply_subscription,
    ensure_customer,
    plan_from_subscription_status,
    require_stripe,
    stripe_error,
    stripe_ready,
)
from .config import settings
from .database import IS_SQLITE, Base, engine, get_db, migrate_schema
from .emailer import email_configured, send_email
from .models import Appointment, Availability, User
from .schemas import (
    AppointmentOut,
    AvailabilityItem,
    BookRequest,
    BusinessOut,
    BusinessUpdate,
    ChangePasswordRequest,
    CheckoutResponse,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    LoginRequest,
    MessageResponse,
    PortalResponse,
    PublicBusinessOut,
    RegisterRequest,
    ResetPasswordRequest,
    SlotOut,
    TokenResponse,
)
from .slots import default_availability_rows, get_open_slots


def confirmed_booking_count(db: Session, user_id: int) -> int:
    return (
        db.query(Appointment)
        .filter(Appointment.user_id == user_id, Appointment.status == "confirmed")
        .count()
    )


def can_accept_bookings(db: Session, user: User) -> bool:
    if (user.plan_status or "free") == "active":
        return True
    return confirmed_booking_count(db, user.id) < settings.free_booking_limit


Base.metadata.create_all(bind=engine)
migrate_schema()

app = FastAPI(title="Calvio API", version="0.1.0")

frontend_origin = (settings.frontend_url or "").rstrip("/")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        frontend_origin,
        "https://calvio-three.vercel.app",
        "http://127.0.0.1:5173",
        "http://localhost:5173",
    ],
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def business_out(user: User) -> BusinessOut:
    availability = [
        AvailabilityItem(
            day_of_week=row.day_of_week,
            start_minute=row.start_minute,
            end_minute=row.end_minute,
            is_open=row.is_open,
        )
        for row in sorted(user.availability, key=lambda r: r.day_of_week)
    ]
    plan_status = user.plan_status or "free"
    is_pro = plan_status == "active"
    used = sum(1 for appt in user.appointments if appt.status == "confirmed")
    remaining = None if is_pro else max(settings.free_booking_limit - used, 0)
    return BusinessOut(
        id=user.id,
        email=user.email,
        business_name=user.business_name,
        slug=user.slug,
        bio=user.bio or "",
        slot_minutes=user.slot_minutes,
        plan_status=plan_status,
        is_pro=is_pro,
        bookings_used=used,
        bookings_limit=settings.free_booking_limit,
        bookings_remaining=remaining,
        availability=availability,
    )


@app.get("/api/health")
def health():
    return {
        "ok": True,
        "product": "Calvio",
        "database": "sqlite" if IS_SQLITE else "postgres",
        "email": email_configured(),
    }


@app.post("/api/auth/register", response_model=TokenResponse)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    slug = slugify(payload.slug)
    if len(slug) < 2:
        raise HTTPException(status_code=400, detail="Slug must use letters or numbers")

    if db.query(User).filter(User.email == payload.email.lower()).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    if db.query(User).filter(User.slug == slug).first():
        raise HTTPException(status_code=400, detail="That booking link is taken")

    user = User(
        email=payload.email.lower(),
        password_hash=hash_password(payload.password),
        business_name=payload.business_name.strip(),
        slug=slug,
        bio="",
        slot_minutes=30,
    )
    db.add(user)
    db.flush()
    for row in default_availability_rows(user.id):
        db.add(row)
    db.commit()
    db.refresh(user)
    return TokenResponse(access_token=create_access_token(user.id))


@app.post("/api/auth/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email.lower()).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return TokenResponse(access_token=create_access_token(user.id))


@app.post("/api/auth/forgot-password", response_model=ForgotPasswordResponse)
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """Always return the same message so emails can't be guessed."""
    generic = "If that email is registered, we sent a password reset link."
    user = db.query(User).filter(User.email == payload.email.lower()).first()
    if not user:
        return ForgotPasswordResponse(message=generic)

    raw_token, token_hash, expires = create_password_reset_token()
    user.reset_token_hash = token_hash
    user.reset_token_expires = expires
    db.commit()

    reset_url = f"{settings.frontend_url}/reset-password?token={raw_token}"
    send_email(
        user.email,
        "Reset your Calvio password",
        (
            "Reset your Calvio password using this link (expires in 1 hour):\n\n"
            f"{reset_url}\n\n"
            "If you did not ask for this, you can ignore this email.\n"
        ),
    )

    # Without SMTP, email only prints in logs — also return the link so you can test.
    if not email_configured():
        return ForgotPasswordResponse(message=generic, reset_url=reset_url)
    return ForgotPasswordResponse(message=generic)


@app.post("/api/auth/reset-password", response_model=MessageResponse)
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    token_hash = hash_reset_token(payload.token)
    user = db.query(User).filter(User.reset_token_hash == token_hash).first()
    if (
        not user
        or not user.reset_token_expires
        or user.reset_token_expires < datetime.utcnow()
    ):
        raise HTTPException(status_code=400, detail="Reset link is invalid or expired")

    user.password_hash = hash_password(payload.password)
    user.reset_token_hash = None
    user.reset_token_expires = None
    db.commit()
    return MessageResponse(message="Password updated. You can log in now.")


@app.post("/api/me/change-password", response_model=MessageResponse)
def change_password(
    payload: ChangePasswordRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not verify_password(payload.current_password, user.password_hash):
        raise HTTPException(status_code=400, detail="Current password is wrong")
    user.password_hash = hash_password(payload.new_password)
    user.reset_token_hash = None
    user.reset_token_expires = None
    db.commit()
    return MessageResponse(message="Password changed.")


@app.get("/api/me", response_model=BusinessOut)
def me(user: User = Depends(get_current_user)):
    return business_out(user)


@app.put("/api/me", response_model=BusinessOut)
def update_me(
    payload: BusinessUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if payload.business_name is not None:
        user.business_name = payload.business_name.strip()
    if payload.bio is not None:
        user.bio = payload.bio.strip()
    if payload.slot_minutes is not None:
        user.slot_minutes = payload.slot_minutes
    db.commit()
    db.refresh(user)
    return business_out(user)


@app.put("/api/me/availability", response_model=BusinessOut)
def update_availability(
    payload: list[AvailabilityItem],
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if len(payload) != 7:
        raise HTTPException(status_code=400, detail="Send all 7 days of the week")

    by_day = {item.day_of_week: item for item in payload}
    if set(by_day.keys()) != set(range(7)):
        raise HTTPException(status_code=400, detail="Each day_of_week 0-6 is required once")

    for row in user.availability:
        item = by_day[row.day_of_week]
        if item.end_minute <= item.start_minute and item.is_open:
            raise HTTPException(status_code=400, detail="End time must be after start time")
        row.start_minute = item.start_minute
        row.end_minute = item.end_minute
        row.is_open = item.is_open

    db.commit()
    db.refresh(user)
    return business_out(user)


@app.get("/api/me/appointments", response_model=list[AppointmentOut])
def my_appointments(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = (
        db.query(Appointment)
        .filter(Appointment.user_id == user.id)
        .order_by(Appointment.starts_at.asc())
        .all()
    )
    return rows


@app.post("/api/me/appointments/{appointment_id}/cancel", response_model=AppointmentOut)
def cancel_appointment(
    appointment_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    appointment = (
        db.query(Appointment)
        .filter(Appointment.id == appointment_id, Appointment.user_id == user.id)
        .first()
    )
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    if appointment.status == "canceled":
        raise HTTPException(status_code=400, detail="That booking is already canceled")
    if appointment.starts_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Past appointments can't be canceled")

    appointment.status = "canceled"
    db.commit()
    db.refresh(appointment)

    when = appointment.starts_at.strftime("%A, %b %d at %I:%M %p")
    send_email(
        appointment.client_email,
        f"Canceled: {user.business_name}",
        (
            f"Your appointment with {user.business_name} was canceled.\n\n"
            f"When it was: {when}\n"
            "If you still need a time, book again on their Calvio page.\n"
        ),
    )
    send_email(
        user.email,
        f"Canceled booking: {appointment.client_name}",
        (
            f"You canceled a booking for {user.business_name}.\n\n"
            f"Client: {appointment.client_name}\n"
            f"Email: {appointment.client_email}\n"
            f"When: {when}\n"
        ),
    )
    return appointment


@app.post("/api/billing/checkout", response_model=CheckoutResponse)
def create_checkout(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    require_stripe()
    if (user.plan_status or "free") == "active":
        raise HTTPException(status_code=400, detail="You already have Calvio Pro")

    try:
        customer_id = ensure_customer(db, user)
        session = stripe.checkout.Session.create(
            mode="subscription",
            customer=customer_id,
            line_items=[{"price": settings.stripe_price_id, "quantity": 1}],
            success_url=f"{frontend_origin}/dashboard?billing=success",
            cancel_url=f"{frontend_origin}/dashboard?billing=cancel",
            client_reference_id=str(user.id),
            metadata={"user_id": str(user.id)},
            subscription_data={"metadata": {"user_id": str(user.id)}},
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise stripe_error(exc) from exc
    if not session.url:
        raise HTTPException(status_code=500, detail="Could not start Stripe Checkout")
    return CheckoutResponse(url=session.url)


@app.post("/api/billing/portal", response_model=PortalResponse)
def create_portal(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    require_stripe()
    try:
        customer_id = ensure_customer(db, user)
        session = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=f"{frontend_origin}/dashboard",
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise stripe_error(exc) from exc
    return PortalResponse(url=session.url)


@app.post("/api/billing/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    if not settings.stripe_webhook_secret:
        raise HTTPException(status_code=503, detail="Stripe webhook secret is not configured")

    stripe.api_key = settings.stripe_secret_key
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, settings.stripe_webhook_secret)
    except Exception as exc:
        if type(exc).__name__ == "SignatureVerificationError":
            raise HTTPException(status_code=400, detail="Invalid signature") from exc
        if isinstance(exc, ValueError):
            raise HTTPException(status_code=400, detail="Invalid payload") from exc
        raise

    event_type = event["type"]
    data = event["data"]["object"]

    if event_type == "checkout.session.completed":
        user_id = (data.get("metadata") or {}).get("user_id") or data.get("client_reference_id")
        subscription_id = data.get("subscription")
        customer_id = data.get("customer")
        user = db.query(User).filter(User.id == int(user_id)).first() if user_id else None
        if user:
            if customer_id:
                user.stripe_customer_id = customer_id
            if subscription_id:
                subscription = stripe.Subscription.retrieve(subscription_id)
                apply_subscription(db, user, subscription)
            else:
                user.plan_status = "active"
                db.commit()

    elif event_type in ("customer.subscription.updated", "customer.subscription.deleted"):
        user = None
        metadata = data.get("metadata") or {}
        if metadata.get("user_id"):
            user = db.query(User).filter(User.id == int(metadata["user_id"])).first()
        if not user and data.get("id"):
            user = db.query(User).filter(User.stripe_subscription_id == data["id"]).first()
        if not user and data.get("customer"):
            user = db.query(User).filter(User.stripe_customer_id == data["customer"]).first()
        if user:
            user.stripe_subscription_id = data.get("id") or user.stripe_subscription_id
            user.plan_status = plan_from_subscription_status(data.get("status"))
            if event_type == "customer.subscription.deleted":
                user.plan_status = "canceled"
            db.commit()

    return {"received": True}


@app.get("/api/billing/status")
def billing_status():
    return {"stripe_configured": stripe_ready()}


@app.get("/api/public/{slug}", response_model=PublicBusinessOut)
def public_business(slug: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.slug == slugify(slug)).first()
    if not user:
        raise HTTPException(status_code=404, detail="Booking page not found")
    return PublicBusinessOut(
        business_name=user.business_name,
        slug=user.slug,
        bio=user.bio or "",
        slot_minutes=user.slot_minutes,
        accepting_bookings=can_accept_bookings(db, user),
    )


@app.get("/api/public/{slug}/slots", response_model=list[SlotOut])
def public_slots(
    slug: str,
    day: date = Query(...),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.slug == slugify(slug)).first()
    if not user:
        raise HTTPException(status_code=404, detail="Booking page not found")
    if day < date.today() or not can_accept_bookings(db, user):
        return []
    return [SlotOut(starts_at=start, ends_at=end) for start, end in get_open_slots(db, user, day)]


@app.post("/api/public/{slug}/book", response_model=AppointmentOut, status_code=status.HTTP_201_CREATED)
def public_book(slug: str, payload: BookRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.slug == slugify(slug)).first()
    if not user:
        raise HTTPException(status_code=404, detail="Booking page not found")
    if not can_accept_bookings(db, user):
        raise HTTPException(
            status_code=403,
            detail="This business has used its 2 free bookings. Ask them to upgrade to Calvio Pro.",
        )

    starts_at = payload.starts_at.replace(tzinfo=None)
    ends_at = starts_at + timedelta(minutes=user.slot_minutes)
    open_slots = get_open_slots(db, user, starts_at.date())
    if (starts_at, ends_at) not in open_slots:
        raise HTTPException(status_code=400, detail="That time is no longer available")

    appointment = Appointment(
        user_id=user.id,
        client_name=payload.client_name.strip(),
        client_email=payload.client_email.lower(),
        starts_at=starts_at,
        ends_at=ends_at,
        notes=(payload.notes or "").strip(),
        status="confirmed",
    )
    db.add(appointment)
    db.commit()
    db.refresh(appointment)

    when = starts_at.strftime("%A, %b %d at %I:%M %p")
    owner_body = (
        f"New booking for {user.business_name}\n\n"
        f"Client: {appointment.client_name}\n"
        f"Email: {appointment.client_email}\n"
        f"When: {when}\n"
        f"Notes: {appointment.notes or '—'}\n"
    )
    client_body = (
        f"You're booked with {user.business_name}!\n\n"
        f"When: {when}\n"
        f"If you need to change anything, reply to this email or contact the business.\n"
    )
    send_email(user.email, f"New booking: {appointment.client_name}", owner_body)
    send_email(appointment.client_email, f"Confirmed: {user.business_name}", client_body)
    return appointment
