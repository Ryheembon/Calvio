from datetime import date, datetime, timedelta

from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .auth import create_access_token, get_current_user, hash_password, slugify, verify_password
from .config import settings
from .database import Base, engine, get_db
from .emailer import send_email
from .models import Appointment, Availability, User
from .schemas import (
    AppointmentOut,
    AvailabilityItem,
    BookRequest,
    BusinessOut,
    BusinessUpdate,
    LoginRequest,
    PublicBusinessOut,
    RegisterRequest,
    SlotOut,
    TokenResponse,
)
from .slots import default_availability_rows, get_open_slots

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Calvio API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://127.0.0.1:5173"],
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
    return BusinessOut(
        id=user.id,
        email=user.email,
        business_name=user.business_name,
        slug=user.slug,
        bio=user.bio or "",
        slot_minutes=user.slot_minutes,
        availability=availability,
    )


@app.get("/api/health")
def health():
    return {"ok": True, "product": "Calvio"}


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
    if day < date.today():
        return []
    return [SlotOut(starts_at=start, ends_at=end) for start, end in get_open_slots(db, user, day)]


@app.post("/api/public/{slug}/book", response_model=AppointmentOut, status_code=status.HTTP_201_CREATED)
def public_book(slug: str, payload: BookRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.slug == slugify(slug)).first()
    if not user:
        raise HTTPException(status_code=404, detail="Booking page not found")

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
