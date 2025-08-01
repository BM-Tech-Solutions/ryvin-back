from datetime import datetime
from typing import Optional
from uuid import UUID

import phonenumbers
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.core.security import utc_now
from app.models.enums import SubscriptionType


class UserBase(BaseModel):
    """
    Base schema for user data
    """

    model_config = ConfigDict(from_attributes=True)

    phone_number: str
    email: Optional[EmailStr] = None

    @field_validator("phone_number")
    def validate_phone_number(cls, v):
        try:
            phone_number = phonenumbers.parse(v, None)
            if not phonenumbers.is_valid_number(phone_number):
                raise ValueError("Invalid phone number")
            return v
        except Exception:
            raise ValueError("Invalid phone number format")


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
    subscription_type: str = Field(default=SubscriptionType.FREE.value)
    subscription_expires_at: Optional[datetime] = None


class UserInDB(UserInDBBase):
    """
    Schema for user in DB (internal use)
    """

    pass


class UserOut(UserInDBBase):
    """
    Schema for user response
    """

    @field_validator("phone_number")
    def validate_phone_number(cls, v):
        return v


class TestUserCreate(BaseModel):
    phone_number: str = Field(default="+442083661177")
    email: Optional[EmailStr] = None
    is_verified: bool = True
    has_completed_questionnaire: bool = False
    is_active: bool = True
    is_admin: bool = True
    last_login: datetime = Field(default_factory=utc_now)
    subscription_type: SubscriptionType
    subscription_expires_at: Optional[datetime] = None

    @field_validator("phone_number")
    def validate_phone_number(cls, v):
        try:
            phone_number = phonenumbers.parse(v, None)
            if not phonenumbers.is_valid_number(phone_number):
                raise ValueError("Invalid phone number")
            return v
        except Exception:
            raise ValueError("Invalid phone number format")
