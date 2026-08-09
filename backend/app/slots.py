from datetime import date, datetime, timedelta

from sqlalchemy.orm import Session

from .models import Appointment, Availability, User


def default_availability_rows(user_id: int) -> list[Availability]:
    rows = []
    for day in range(7):
        is_open = day < 5  # Mon-Fri open by default
        rows.append(
            Availability(
                user_id=user_id,
                day_of_week=day,
                start_minute=9 * 60,
                end_minute=17 * 60,
                is_open=is_open,
            )
        )
    return rows


def get_open_slots(db: Session, user: User, day: date) -> list[tuple[datetime, datetime]]:
    weekday = day.weekday()  # Monday=0
    availability = (
        db.query(Availability)
        .filter(Availability.user_id == user.id, Availability.day_of_week == weekday)
        .first()
    )
    if not availability or not availability.is_open:
        return []

    slot_minutes = user.slot_minutes
    start = datetime.combine(day, datetime.min.time()) + timedelta(minutes=availability.start_minute)
    end = datetime.combine(day, datetime.min.time()) + timedelta(minutes=availability.end_minute)
    now = datetime.now()

    existing = (
        db.query(Appointment)
        .filter(
            Appointment.user_id == user.id,
            Appointment.status == "confirmed",
            Appointment.starts_at >= start,
            Appointment.starts_at < end,
        )
        .all()
    )
    taken = {(a.starts_at, a.ends_at) for a in existing}

    slots = []
    cursor = start
    while cursor + timedelta(minutes=slot_minutes) <= end:
        slot_end = cursor + timedelta(minutes=slot_minutes)
        if cursor > now and (cursor, slot_end) not in taken:
            # also reject overlap with any existing appointment
            overlaps = any(
                cursor < existing_end and slot_end > existing_start
                for existing_start, existing_end in taken
            )
            if not overlaps:
                slots.append((cursor, slot_end))
        cursor += timedelta(minutes=slot_minutes)
    return slots
