from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    business_name: str = Field(min_length=2, max_length=120)
    slug: str = Field(min_length=2, max_length=80)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class AvailabilityItem(BaseModel):
    day_of_week: int = Field(ge=0, le=6)
    start_minute: int = Field(ge=0, le=24 * 60)
    end_minute: int = Field(ge=0, le=24 * 60)
    is_open: bool = True


class BusinessUpdate(BaseModel):
    business_name: Optional[str] = Field(default=None, min_length=2, max_length=120)
    bio: Optional[str] = None
    slot_minutes: Optional[int] = Field(default=None, ge=15, le=180)


class BusinessOut(BaseModel):
    id: int
    email: EmailStr
    business_name: str
    slug: str
    bio: str
    slot_minutes: int
    availability: list[AvailabilityItem]

    class Config:
        from_attributes = True


class PublicBusinessOut(BaseModel):
    business_name: str
    slug: str
    bio: str
    slot_minutes: int


class SlotOut(BaseModel):
    starts_at: datetime
    ends_at: datetime


class BookRequest(BaseModel):
    client_name: str = Field(min_length=2, max_length=120)
    client_email: EmailStr
    starts_at: datetime
    notes: str = ""


class AppointmentOut(BaseModel):
    id: int
    client_name: str
    client_email: EmailStr
    starts_at: datetime
    ends_at: datetime
    notes: str
    status: str

    class Config:
        from_attributes = True
