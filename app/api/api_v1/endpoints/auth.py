"""
Authentication Endpoints
-----------------------
Endpoints for Firebase phone authentication flow with simplified implementation.
"""
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Security
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.main import api_key_header
from app.services.auth_service import AuthService
from app.models.user import User


# Request models
class VerifyUserRequest(BaseModel):
    phone_number: str = Field(..., description="Phone number in E.164 format, e.g. '+213778788714'")


class VerifyPhoneRequest(BaseModel):
    firebase_token: str = Field(..., description="Firebase ID token")


class CompleteProfileRequest(BaseModel):
    access_token: str = Field(..., description="Access token received from verify-phone endpoint")
    name: str
    email: EmailStr
    profile_image: Optional[str] = None


class RegisterRequest(BaseModel):
    firebase_token: str = Field(..., description="Firebase ID token from verification")
    device_info: Optional[Dict[str, str]] = Field(default=None, description="Device information")


class LoginRequest(BaseModel):
    firebase_token: str = Field(..., description="Firebase ID token")
    device_info: Optional[Dict[str, str]] = Field(default=None, description="Device information")


class RefreshTokenRequest(BaseModel):
    refresh_token: str


# Response models
class VerifyUserResponse(BaseModel):
    exists: bool
    user_id: Optional[str] = None
    phone_number: str


class VerifyPhoneResponse(BaseModel):
    firebase_uid: str
    phone_number: str
    is_verified: bool


class CompleteProfileResponse(BaseModel):
    user_id: str
    name: str
    email: str
    profile_image: Optional[str] = None
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RegisterResponse(BaseModel):
    user_id: str
    phone_number: str
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class LoginResponse(BaseModel):
    user_id: str
    phone_number: str
    name: Optional[str] = None
    email: Optional[str] = None
    profile_image: Optional[str] = None
    profile_complete: bool
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class LogoutResponse(BaseModel):
    message: str


router = APIRouter()


@router.post("/verify-user", response_model=VerifyUserResponse)
def verify_user(
    request: VerifyUserRequest,
    db: Session = Depends(get_db),
    api_key: str = Security(api_key_header)
) -> Any:
    """
    Verify if a user exists with the given phone number
    """
    auth_service = AuthService(db)
    return auth_service.verify_user_exists(request.phone_number)


@router.post("/verify-phone", response_model=VerifyPhoneResponse)
def verify_phone(
    request: VerifyPhoneRequest,
    db: Session = Depends(get_db),
    api_key: str = Security(api_key_header)
) -> Any:
    """
    Verify phone number with Firebase ID token (only verification, no user creation)
    """
    auth_service = AuthService(db)
    return auth_service.verify_phone_token(request.firebase_token)


@router.post("/complete-profile", response_model=CompleteProfileResponse)
def complete_profile(
    request: CompleteProfileRequest,
    db: Session = Depends(get_db),
    api_key: str = Security(api_key_header)
) -> Any:
    """
    Complete user profile after phone verification
    """
    auth_service = AuthService(db)
    return auth_service.complete_profile(
        access_token=request.access_token,
        name=request.name,
        email=request.email,
        profile_image=request.profile_image
    )


@router.post("/register", response_model=RegisterResponse)
def register(
    request: RegisterRequest,
    db: Session = Depends(get_db),
    api_key: str = Security(api_key_header)
) -> Any:
    """
    Register a new user with Firebase token after verification
    """
    auth_service = AuthService(db)
    return auth_service.register_user(
        firebase_token=request.firebase_token,
        device_info=request.device_info
    )


@router.post("/login", response_model=LoginResponse)
def login(
    request: LoginRequest,
    db: Session = Depends(get_db),
    api_key: str = Security(api_key_header)
) -> Any:
    """
    Login with Firebase token
    """
    auth_service = AuthService(db)
    return auth_service.login_user(
        firebase_token=request.firebase_token,
        device_info=request.device_info
    )


@router.post("/refresh-token", response_model=TokenResponse)
def refresh_token(
    request: RefreshTokenRequest,
    db: Session = Depends(get_db)
) -> Any:
    """
    Refresh access token
    """
    auth_service = AuthService(db)
    return auth_service.refresh_tokens(request.refresh_token)


@router.post("/logout", response_model=LogoutResponse)
def logout(
    request: RefreshTokenRequest,
    db: Session = Depends(get_db)
) -> Any:
    """
    Logout user by revoking refresh token
    """
    auth_service = AuthService(db)
    return auth_service.logout(request.refresh_token)


@router.get("/test-token/{phone_number}")
def get_test_token(
    phone_number: str,
    db: Session = Depends(get_db),
    api_key: str = Security(api_key_header)
) -> Dict[str, str]:
    """
    Generate a test Firebase ID token for a given phone number.
    This endpoint is for testing purposes only.
    
    Use with the test phone numbers configured in Firebase console:
    - +213 655 55 55 55 (code: 123456)
    - +213 778 78 87 14 (code: 123123)
    """
    auth_service = AuthService(db)
    token = auth_service.generate_test_token(phone_number)
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate test token"
        )
    
    return {"firebase_token": token}


@router.get("/test-user/{user_id}")
def get_user_data(
    user_id: str,
    db: Session = Depends(get_db),
    api_key: str = Security(api_key_header)
) -> Dict[str, Any]:
    """
    Get user data by ID for testing purposes.
    """
    try:
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Convert user object to dictionary
        user_data = {
            "id": str(user.id),
            "phone": user.phone,
            "name": user.name,
            "email": user.email,
            "profile_image": user.profile_image,
            "firebase_uid": user.firebase_uid,
            "is_verified": user.is_verified,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "last_login": user.last_login.isoformat() if user.last_login else None,
            "device_id": user.device_id,
            "platform": user.platform
        }
        
        return {"user": user_data}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving user data: {str(e)}"
        )
