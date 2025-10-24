"""
Authentication Endpoints
-----------------------
Endpoints for Firebase phone authentication and Google OAuth.
"""

from typing import Annotated, Any, Dict

import httpx
from fastapi import APIRouter, Body, Depends, Form, HTTPException, Security, status

# Firebase Admin SDK
from firebase_admin import auth as firebase_auth
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import SessionDep, VerifiedUserDep
from app.main import api_key_header
from app.models.user import User
from app.schemas.auth import (
    AdminLoginRequest,
    AuthResponse,
    CompleteProfileRequest,
    CompleteProfileResponse,
    GoogleAuthRequest,
    LogoutResponse,
    PhoneAuthRequest,
    RefreshTokenRequest,
    TokenResponse,
    UpdatePhoneRequest,
)
from app.schemas.user import UserOut
from app.services.auth_service import AuthService
from firebase import init_firebase

router = APIRouter()


@router.post("/phone-auth", response_model=AuthResponse)
def phone_auth(
    request: PhoneAuthRequest,
    db: SessionDep,
    api_key: str = Security(api_key_header),
) -> dict:
    """
    Authenticate with phone number.

    Note: Firebase token verification is handled in the frontend.

    1. Checks if user exists
    2. Creates account if user doesn't exist
    3. Returns login info in both cases
    """
    auth_service = AuthService(db)
    update_token = "firebase_token" in request.model_dump(exclude_unset=True)
    return auth_service.phone_auth(
        phone_region=request.phone_region,
        phone_number=request.phone_number,
        firebase_token=request.firebase_token,
        update_token=update_token,
    )


@router.post("/google-auth")
async def google_auth(
    request: GoogleAuthRequest,
    db: Session = Depends(get_db),
    api_key: str = Security(api_key_header),
) -> dict:
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
    update_token = "firebase_token" in request.model_dump(exclude_unset=True)
    return await auth_service.google_auth(
        id_token=request.id_token,
        firebase_token=request.firebase_token,
        update_token=update_token,
    )


@router.post("/admin-login")
async def admin_login(
    request: AdminLoginRequest,
    session: SessionDep,
    api_key: str = Security(api_key_header),
) -> dict:
    """
    login endpoint for the Admin
    """
    auth_service = AuthService(session)
    return await auth_service.admin_login(email=request.email, password=request.password)


@router.post("/set-firebase-token", response_model=UserOut)
def sef_firebase_token(
    current_user: VerifiedUserDep,
    session: SessionDep,
    firebase_token: Annotated[str, Body(embed=True)],
    api_key: str = Security(api_key_header),
) -> UserOut:
    current_user.firebase_token = firebase_token
    session.commit()
    return current_user


@router.post("/complete-profile", response_model=CompleteProfileResponse)
async def complete_profile(
    current_user: VerifiedUserDep,
    session: SessionDep,
    request: CompleteProfileRequest = Form(media_type="multipart/form-data"),
    api_key: str = Security(api_key_header),
) -> CompleteProfileResponse:
    """
    Complete user profile after authentication
    """
    auth_service = AuthService(session)
    auth_service.can_complete_profile(current_user, request)
    return await auth_service.complete_profile(current_user, request)


@router.post("/update-phone-number", response_model=UserOut)
def update_phone_number(
    request: UpdatePhoneRequest,
    current_user: VerifiedUserDep,
    session: SessionDep,
    api_key: str = Security(api_key_header),
) -> UserOut:
    """
    Change current user phone number
    """
    auth_service = AuthService(session)
    return auth_service.update_phone(current_user, request)


@router.post("/refresh-token", response_model=TokenResponse)
def refresh_token(request: RefreshTokenRequest, db: Session = Depends(get_db)) -> Any:
    """
    Refresh access token
    """
    auth_service = AuthService(db)
    return auth_service.refresh_tokens(request.refresh_token)


@router.post("/logout", response_model=LogoutResponse)
def logout(request: RefreshTokenRequest, db: Session = Depends(get_db)) -> Any:
    """
    Logout user by revoking refresh token
    """
    auth_service = AuthService(db)
    return auth_service.logout(request.refresh_token)


@router.get("/test-token/{phone_number}")
def get_test_token(
    phone_number: str,
    db: Session = Depends(get_db),
    api_key: str = Security(api_key_header),
) -> Dict[str, str]:
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
    email: str, db: Session = Depends(get_db), api_key: str = Security(api_key_header)
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
        # Ensure Firebase is initialized (defensive)
        init_firebase()
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
    user_id: str, db: Session = Depends(get_db), api_key: str = Security(api_key_header)
) -> Dict[str, Any]:
    """
    Get user data by ID for testing purposes.
    """
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Convert user object to dictionary
    user_data = {
        "id": str(user.id),
        "phone_region": user.phone_region,
        "phone_number": user.phone_number,
        "email": user.email,
        "name": user.name,
        "is_verified": user.is_verified,
        "created_at": user.created_at.isoformat(),
        "last_login": user.last_login.isoformat() if user.last_login else None,
    }

    return {"user": user_data}
