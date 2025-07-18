"""
Authentication Endpoints
-----------------------
Endpoints for Firebase phone authentication and Google OAuth.
"""

from typing import Any, Dict, Optional
from uuid import UUID

import httpx
from fastapi import APIRouter, HTTPException, Security, status
from firebase_admin import auth as firebase_auth
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.exc import IntegrityError

from app.core.dependencies import SessionDep
from app.main import api_key_header
from app.models.user import User
from app.schemas.user import TestUserCreate, UserOut
from app.services.auth_service import AuthService


# Request models
class PhoneAuthRequest(BaseModel):
    phone_number: str = Field(..., description="User's phone number")
    device_info: Optional[Dict[str, str]] = Field(default=None, description="Device information")


class GoogleAuthRequest(BaseModel):
    google_token: str = Field(..., description="Google OAuth access token")
    device_info: Optional[Dict[str, str]] = Field(default=None, description="Device information")


class CompleteProfileRequest(BaseModel):
    access_token: str = Field(..., description="Access token received from auth endpoint")
    name: str
    email: EmailStr
    profile_image: Optional[str] = None


class RefreshTokenRequest(BaseModel):
    refresh_token: str


# Response models
class AuthResponse(BaseModel):
    user_id: str
    phone_number: Optional[str] = None
    email: Optional[str] = None
    name: Optional[str] = None
    profile_image: Optional[str] = None
    is_new_user: bool
    is_profile_complete: bool
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class CompleteProfileResponse(BaseModel):
    user_id: str
    name: str
    email: str
    profile_image: Optional[str] = None
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


@router.post("/phone-auth", response_model=AuthResponse)
def phone_auth(
    db: SessionDep,
    request: PhoneAuthRequest,
    api_key: str = Security(api_key_header),
) -> Any:
    """
    Authenticate with phone number.

    Note: Firebase token verification is handled in the frontend.

    1. Checks if user exists
    2. Creates account if user doesn't exist
    3. Returns login info in both cases
    """
    auth_service = AuthService(db)
    return auth_service.phone_auth(
        phone_number=request.phone_number, device_info=request.device_info
    )


@router.post("/google-auth", response_model=AuthResponse)
def google_auth(
    db: SessionDep,
    request: GoogleAuthRequest,
    api_key: str = Security(api_key_header),
) -> Any:
    """
    Authenticate with Google OAuth token.
    Handles both new and existing users.

    1. Verifies Google token
    2. Retrieves user data from Google
    3. Checks if email exists in our system
    4. Creates account if user doesn't exist
    5. Returns login info in both cases
    """
    auth_service = AuthService(db)
    return auth_service.google_auth(
        google_token=request.google_token, device_info=request.device_info
    )


@router.post("/complete-profile", response_model=CompleteProfileResponse)
def complete_profile(
    request: CompleteProfileRequest,
    db: SessionDep,
    api_key: str = Security(api_key_header),
) -> Any:
    """
    Complete user profile after authentication
    """
    auth_service = AuthService(db)
    return auth_service.complete_profile(
        access_token=request.access_token,
        name=request.name,
        email=request.email,
        profile_image=request.profile_image,
    )


@router.post("/refresh-token", response_model=TokenResponse)
def refresh_token(request: RefreshTokenRequest, db: SessionDep) -> Any:
    """
    Refresh access token
    """
    auth_service = AuthService(db)
    return auth_service.refresh_tokens(request.refresh_token)


@router.post("/logout", response_model=LogoutResponse)
def logout(request: RefreshTokenRequest, db: SessionDep) -> Any:
    """
    Logout user by revoking refresh token
    """
    auth_service = AuthService(db)
    return auth_service.logout(request.refresh_token)


@router.get("/test-token/{phone_number}")
def get_test_token(phone_number: str, api_key: str = Security(api_key_header)) -> Dict[str, str]:
    """
    Generate a test token for a given phone number.
    This endpoint is for testing purposes only.

    Use with test phone numbers:
    - +213 655 55 55 55
    - +213 778 78 87 14
    """
    # In the new flow, we don't need to generate Firebase tokens
    # The frontend will handle the verification
    return {
        "message": "In the new flow, the frontend handles phone verification. Use the phone number directly with the /phone-auth endpoint.",
        "phone_number": phone_number,
    }


@router.get("/test-google-token/{email}")
async def get_test_google_token(
    email: str, api_key: str = Security(api_key_header)
) -> Dict[str, Any]:
    """
    Generate a test Firebase ID token for a given email.
    This endpoint is for testing purposes only.

    Note: This creates a real Firebase user and generates a real ID token.
    Use only in development/staging environments.

    Test emails:
    - test1@example.com
    - test2@example.com
    """
    try:
        # Check if user exists in Firebase Auth
        try:
            user = firebase_auth.get_user_by_email(email)
            # User exists, generate a custom token
            custom_token = firebase_auth.create_custom_token(user.uid).decode("utf-8")
        except (ValueError, firebase_auth.UserNotFoundError):
            # Create a new test user in Firebase Auth
            user = firebase_auth.create_user(
                email=email,
                email_verified=True,
                display_name=email.split("@")[0].replace(".", " ").title(),
                photo_url=f"https://ui-avatars.com/api/?name={email[0].upper()}&background=random",
            )
            custom_token = firebase_auth.create_custom_token(user.uid).decode("utf-8")

        # Exchange custom token for ID token
        id_token = await exchange_custom_token_for_id_token(custom_token)

        return {
            "message": "Test Firebase ID token generated successfully. FOR TESTING ONLY.",
            "email": email,
            "id_token": id_token,
            "uid": user.uid,
            "name": user.display_name or email.split("@")[0].replace(".", " ").title(),
            "picture": user.photo_url,
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating test token: {str(e)}",
        )


async def exchange_custom_token_for_id_token(custom_token: str) -> str:
    """
    Exchange a Firebase custom token for an ID token using the Firebase REST API.
    """
    from app.core.config import settings

    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithCustomToken?key={settings.FIREBASE_API_KEY}"

    payload = {"token": custom_token, "returnSecureToken": True}

    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
        return data["idToken"]


@router.get("/test-user/{user_id}")
def get_user_data(
    db: SessionDep, user_id: UUID, api_key: str = Security(api_key_header)
) -> Dict[str, Any]:
    """
    Get user data by ID for testing purposes.
    """
    try:
        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        # Convert user object to dictionary
        user_data = {
            "id": str(user.id),
            "phone_number": user.phone_number,
            "email": user.email,
            "name": "test_name",
            "is_verified": user.is_verified,
            "created_at": user.created_at.isoformat(),
            "last_login": user.last_login.isoformat() if user.last_login else None,
        }

        return {"user": user_data}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving user data: {str(e)}",
        )


@router.post("/create-user/", tags=["test"])
def create_user(session: SessionDep, user_in: TestUserCreate) -> UserOut:
    """
    Testing endpoint for creating a new user.
    """
    user = session.query(User).filter(User.phone_number == user_in.phone_number).first()
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User with phone number: '{user_in.phone_number}' already exists",
        )
    try:
        user = User(**user_in.model_dump(exclude_unset=True))
        session.add(user)
        session.commit()
        session.refresh(user)
    except IntegrityError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"args": e.args},
        )
    return user
