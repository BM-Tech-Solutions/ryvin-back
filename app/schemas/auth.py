from typing import Annotated, Dict, Optional

from fastapi import UploadFile
from pydantic import AfterValidator, BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.schemas.user import validate_phone_number, validate_phone_region

# validators
PhoneRegion = Annotated[str, AfterValidator(validate_phone_region)]
PhoneNumber = Annotated[str, AfterValidator(validate_phone_number)]


# Request models
class PhoneAuthRequest(BaseModel):
    phone_region: str = Field(description="User's phone number Region")
    phone_number: str = Field(description="User's phone number Number")
    device_info: Optional[Dict[str, str]] = Field(default=None, description="Device information")

    @field_validator("phone_region")
    def validate_phone_region(cls, v):
        return validate_phone_region(v)

    @field_validator("phone_number")
    def validate_phone_number(cls, v):
        return validate_phone_number(v)


class GoogleAuthRequest(BaseModel):
    code: str


class GoogleAuthMobileRequest(BaseModel):
    id_token: str


class UpdatePhoneRequest(BaseModel):
    old_phone_region: PhoneRegion | None = Field(description="User's old phone number Region")
    old_phone_number: PhoneNumber | None = Field(description="User's old phone number Number")
    new_phone_region: PhoneRegion = Field(description="User's new phone number Region")
    new_phone_number: PhoneNumber = Field(description="User's new phone number Number")


class RefreshTokenRequest(BaseModel):
    refresh_token: str


# Response models
class AuthResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    user_id: str
    phone_region: Optional[str] = None
    phone_number: Optional[str] = None
    email: Optional[str] = None
    name: Optional[str] = None
    profile_image: Optional[str] = None
    is_new_user: bool
    is_profile_complete: bool
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class CompleteProfileRequest(BaseModel):
    name: str | None = None
    phone_region: PhoneRegion = None
    phone_number: PhoneNumber = None
    email: EmailStr | None = None
    profile_image: UploadFile | None = None


class CompleteProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    user_id: str
    name: str
    email: Optional[str]
    profile_image: Optional[str] = None
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class LogoutResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    message: str
