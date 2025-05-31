from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, validator
import phonenumbers

from app.models.enums import SubscriptionType


class UserBase(BaseModel):
    """
    Base schema for user data
    """
    phone_number: str
    email: Optional[EmailStr] = None
    
    @validator("phone_number")
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
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None
    subscription_type: str = Field(default=SubscriptionType.FREE.value)
    subscription_expires_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserInDB(UserInDBBase):
    """
    Schema for user in DB (internal use)
    """
    pass


class User(UserInDBBase):
    """
    Schema for user response
    """
    pass
