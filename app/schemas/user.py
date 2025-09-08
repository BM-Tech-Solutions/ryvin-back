from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.core.security import utc_now
from app.models.enums import SubscriptionType


def validate_phone_region(v: str) -> str:
    if not isinstance(v, str):
        return v

    if not v.startswith("+"):
        raise ValueError("Phone region must start with '+'.")

    code = v.removeprefix("+")
    if not code.isdigit() or not (1 <= len(code) <= 3):
        raise ValueError("Phone region must be a 1, 2, or 3-digit number.")
    return v


def validate_phone_number(v: str) -> str:
    if not isinstance(v, str):
        return v

    if not v.isdigit() or not (8 <= len(v) <= 9):
        raise ValueError("Phone number must be an 8 or 9-digit number.")
    return v


class UserBase(BaseModel):
    """
    Base schema for user data
    """

    model_config = ConfigDict(from_attributes=True)

    name: str | None
    phone_region: str | None = None
    phone_number: str | None = None
    email: Optional[EmailStr] = None

    @field_validator("phone_region")
    def validate_phone_region(cls, v):
        return validate_phone_region(v)

    @field_validator("phone_number")
    def validate_phone_number(cls, v):
        return validate_phone_number(v)


class UserCreate(UserBase):
    """
    Schema for user creation
    """

    pass


class UserUpdate(BaseModel):
    """
    Schema for user update
    """

    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None


class UserInDBBase(UserBase):
    """
    Base schema for user in DB
    """

    id: UUID
    is_verified: bool
    is_active: bool
    has_completed_questionnaire: bool
    is_admin: bool
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None
    subscription_type: str = Field(default=SubscriptionType.FREE)
    subscription_expires_at: Optional[datetime] = None
    social_provider: Optional[str] = None
    social_id: Optional[str] = None
    social_image: Optional[str] = None


class UserInDB(UserInDBBase):
    """
    Schema for user in DB (internal use)
    """

    pass


class UserOut(UserInDBBase):
    """
    Schema for user response
    """

    @field_validator("phone_region")
    def validate_phone_region(cls, v):
        return v

    @field_validator("phone_number")
    def validate_phone_number(cls, v):
        return v


class TestUserCreate(BaseModel):
    phone_region: str = Field(examples="+442")
    phone_number: str = Field(examples="083661177")
    email: Optional[EmailStr] = None
    is_verified: bool = True
    has_completed_questionnaire: bool = False
    is_active: bool = True
    is_admin: bool = True
    last_login: datetime = Field(default_factory=utc_now)
    subscription_type: SubscriptionType
    subscription_expires_at: Optional[datetime] = None

    @field_validator("phone_region")
    def validate_phone_region(cls, v):
        return validate_phone_region(v)

    @field_validator("phone_number")
    def validate_phone_number(cls, v):
        return validate_phone_number(v)
