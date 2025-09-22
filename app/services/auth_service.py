"""Authentication Service
--------------------
Service for Firebase authentication operations with simplified flow.
"""

import os
import random
import string
import uuid
from datetime import timedelta
from typing import Any, Dict, Optional

import aiofiles
import httpx
import requests
from fastapi import HTTPException, UploadFile, status
from firebase_admin import auth as firebase_auth
from jose import jwt

from app.core.config import settings
from app.core.security import create_access_token, create_refresh_token, utc_now
from app.models.enums import SocialProviders
from app.models.token import RefreshToken
from app.models.user import User
from app.schemas.auth import CompleteProfileRequest, UpdatePhoneRequest
from app.services.base_service import BaseService


class AuthService(BaseService):
    """
    Service for authentication operations with simplified flow
    """

    def can_complete_profile(self, user: User, request: CompleteProfileRequest):
        """
        check whether user can update his profile using this request
        """
        request_data = request.model_dump(exclude_unset=True)

        if (not request.phone_region and request.phone_number) or (
            request.phone_region and not request.phone_number
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="phone_region & phone_number: set both or neither",
            )

        if (
            not user.social_id
            and "phone_region" in request_data
            and user.phone_region != request.phone_region
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="can't update phone_region for phone users",
            )

        if (
            not user.social_id
            and "phone_number" in request_data
            and user.phone_number != request.phone_number
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="can't update phone_number for phone users",
            )

        if user.social_id and "email" in request_data and user.email != request.email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="can't update email for social users",
            )

        if request.name:
            # Check if name is already in use
            same_name_user = (
                self.db.query(User).filter(User.name == request.name, User.id != user.id).first()
            )

            if same_name_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="'name' already in use",
                )

    async def save_image(self, file: UploadFile, dest_path: str) -> str:
        # Validate file type
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in settings.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type not allowed. Allowed types: {', '.join(settings.ALLOWED_EXTENSIONS)}",
            )

        dest_path = f"{dest_path}{file_ext}"
        file_abs_path = settings.BASE_DIR / dest_path

        try:
            # make sure media/photos exists
            os.makedirs(file_abs_path.parent, exist_ok=True)

            # Open the destination file in binary write mode (async)
            async with aiofiles.open(file_abs_path, "wb") as dest_file:
                while chunk := await file.read(8192):
                    await dest_file.write(chunk)

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"There was an error uploading the image: {e}",
            )
        finally:
            # Ensure the uploaded file's internal temporary file is closed
            file.file.close()

        return dest_path

    async def complete_profile(self, user: User, request: CompleteProfileRequest) -> Dict[str, Any]:
        """
        Complete user profile after phone verification
        """
        try:
            # Update user information (name, email, phone)
            user_data = request.model_dump(exclude_unset=True)
            user_data.pop("profile_image", None)

            for key, value in user_data.items():
                setattr(user, key, value)

            self.db.commit()
            self.db.refresh(user)

            if request.profile_image:
                # save the image to filesystem
                file_path = f"media/photos/{uuid.uuid4()}"
                file_path = await self.save_image(request.profile_image, dest_path=file_path)
                old_file_path = user.profile_image
                user.profile_image = file_path

                self.db.commit()
                self.db.refresh(user)

                if old_file_path:
                    try:
                        os.remove(settings.BASE_DIR / old_file_path)
                    except FileNotFoundError:
                        pass

            # Generate new tokens
            access_token = create_access_token(subject=str(user.id))
            refresh_token = self._generate_unique_refresh_token(str(user.id))

            # Store the refresh token in the database
            expires_at = utc_now() + timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)

            # Check if a refresh token already exists for this user
            existing_token = (
                self.db.query(RefreshToken).filter(RefreshToken.user_id == user.id).first()
            )

            if existing_token:
                # Update existing token
                existing_token.token = refresh_token
                existing_token.expires_at = expires_at
                existing_token.is_revoked = False
            else:
                # Create new refresh token record
                db_refresh_token = RefreshToken(
                    id=uuid.uuid4(),
                    user_id=user.id,
                    token=refresh_token,
                    expires_at=expires_at,
                    is_revoked=False,
                )
                self.db.add(db_refresh_token)

            self.db.commit()

            return {
                "user_id": str(user.id),
                "name": user.name,
                "email": user.email,
                "profile_image": user.profile_image,
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
            }

        except Exception as e:
            print(f"Error in complete_profile: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to complete profile: {str(e)}",
            )

    def update_phone(self, user: User, request: UpdatePhoneRequest):
        if user.phone_region != request.old_phone_region:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail={"detail": "wrong old phone region"}
            )
        if user.phone_number != request.old_phone_number:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail={"detail": "wrong old phone number"}
            )

        user.phone_region = request.new_phone_region
        user.phone_number = request.new_phone_number
        self.session.commit()
        self.session.refresh(user)
        return user

    def refresh_tokens(self, refresh_token: str) -> Dict[str, Any]:
        """
        Create new access and refresh tokens using a valid refresh token
        """
        try:
            # Find the refresh token in the database
            db_refresh_token = (
                self.db.query(RefreshToken)
                .filter(
                    RefreshToken.token == refresh_token,
                    RefreshToken.is_revoked.is_(False),
                    RefreshToken.expires_at > utc_now(),
                )
                .first()
            )

            if not db_refresh_token:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired refresh token",
                )

            # Create new tokens
            access_token = create_access_token(subject=str(db_refresh_token.user_id))
            new_refresh_token = self._generate_unique_refresh_token(str(db_refresh_token.user_id))

            # Update the refresh token in the database
            db_refresh_token.token = new_refresh_token
            db_refresh_token.expires_at = utc_now() + timedelta(days=30)

            self.db.commit()

            return {
                "access_token": access_token,
                "refresh_token": new_refresh_token,
                "token_type": "bearer",
            }

        except Exception as e:
            print(f"Error in refresh_tokens: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to refresh tokens: {str(e)}",
            )

    def phone_auth(
        self, phone_region: str, phone_number: str, firebase_token: str
    ) -> Dict[str, Any]:
        """
        Unified phone authentication method that handles both new and existing users.

        1. Checks if user exists
        2. Creates account if user doesn't exist
        3. Returns login info in both cases

        Note: Firebase token verification is handled in the frontend
        """
        if not phone_region:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Phone region is required"
            )
        if not phone_number:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Phone number is required"
            )

        # Check if user exists in our database
        user = (
            self.db.query(User)
            .filter(User.phone_region == phone_region, User.phone_number == phone_number)
            .first()
        )
        is_new_user = user is None

        try:
            if is_new_user:
                # Create new user with null profile fields
                user = User(
                    phone_region=phone_region,
                    phone_number=phone_number,
                    is_verified=True,
                    last_login=utc_now(),
                    name=None,
                    email=None,
                    profile_image=None,
                    firebase_token=firebase_token,
                )
                self.db.add(user)
            else:
                user.firebase_token = firebase_token
                # Update last login timestamp
                user.last_login = utc_now()

            # Device info is accepted but not stored as the User model has no such columns

            self.db.commit()
            self.db.refresh(user)

            # Check if profile is complete
            is_profile_complete = user.name is not None and user.email is not None

            # Generate tokens
            access_token = create_access_token(subject=str(user.id))
            refresh_token = self._generate_unique_refresh_token(str(user.id))

            # Store the refresh token in the database
            expires_at = utc_now() + timedelta(days=30)

            # Check if a refresh token already exists for this user
            existing_token = (
                self.db.query(RefreshToken).filter(RefreshToken.user_id == user.id).first()
            )

            if existing_token:
                # Update existing token
                existing_token.token = refresh_token
                existing_token.expires_at = expires_at
                existing_token.is_revoked = False
            else:
                # Create new refresh token record
                db_refresh_token = RefreshToken(
                    id=uuid.uuid4(),
                    user_id=user.id,
                    token=refresh_token,
                    expires_at=expires_at,
                    is_revoked=False,
                )
                self.db.add(db_refresh_token)

            self.db.commit()

            return {
                "user_id": str(user.id),
                "phone_region": phone_region,
                "phone_number": phone_number,
                "email": user.email,
                "name": user.name,
                "profile_image": user.profile_image,
                "is_new_user": is_new_user,
                "is_profile_complete": is_profile_complete,
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
            }
        except Exception as e:
            print(f"Error in phone_auth: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to authenticate user: {str(e)}",
            )

    async def google_auth(self, id_token, firebase_token):
        """
        decode the ID token without verification and get_or_create an account.
        """
        try:
            decoded_id_token = jwt.get_unverified_claims(id_token)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Token Verification Failed: {e}",
            )

        # Extract user data from the decoded token
        email = decoded_id_token.get("email")
        name = decoded_id_token.get("name", "")
        social_image = decoded_id_token.get("picture", "")
        social_id = decoded_id_token.get("sub")

        user = (
            self.db.query(User)
            .filter(
                User.social_provider == SocialProviders.GOOGLE,
                User.social_id == social_id,
            )
            .first()
        )
        is_new_user = not user
        if is_new_user:
            # create new user
            user = User(
                phone_region=None,
                phone_number=None,
                email=email,
                name=name,
                social_image=social_image,
                is_verified=True,
                last_login=utc_now(),
                social_provider=SocialProviders.GOOGLE,
                social_id=social_id,
                firebase_token=firebase_token,
            )
            self.db.add(user)
        else:
            # Update existing user
            user.firebase_token = firebase_token
            user.last_login = utc_now()
            user.is_verified = True

        self.db.commit()
        self.db.refresh(user)

        # Check if profile is complete
        is_profile_complete = user.name is not None and user.email is not None

        # Generate tokens
        access_token = create_access_token(user.id)
        refresh_token = create_refresh_token(user.id)

        # Store the refresh token in the database
        expires_at = utc_now() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

        # Check if a refresh token already exists for this user
        existing_token = self.db.query(RefreshToken).filter(RefreshToken.user_id == user.id).first()

        if existing_token:
            # Update existing token
            existing_token.token = refresh_token
            existing_token.expires_at = expires_at
            existing_token.is_revoked = False
        else:
            # Create new refresh token record
            db_refresh_token = RefreshToken(
                user_id=user.id,
                token=refresh_token,
                expires_at=expires_at,
                is_revoked=False,
            )
            self.db.add(db_refresh_token)

        self.db.commit()

        return {
            "user_id": str(user.id),
            "phone_region": user.phone_region,
            "phone_number": user.phone_number,
            "email": user.email,
            "name": user.name,
            "profile_image": user.profile_image,
            "is_new_user": is_new_user,
            "is_profile_complete": is_profile_complete,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }

    async def get_google_jwks(self):
        jwks_url = "https://www.googleapis.com/oauth2/v3/certs"
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(jwks_url)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as exc:
            raise Exception(f"Failed to fetch JWKS: {exc.response.text}")

    async def verify_google_id_token(self, id_token: str, access_token: str, client_id: str):
        jwks = await self.get_google_jwks()
        # Get the KID from the token header
        header = jwt.get_unverified_header(id_token)
        kid = header.get("kid")

        if not kid:
            raise Exception("No 'kid' found in token header.")

        # Find the matching key in the JWKS
        key = next((key for key in jwks["keys"] if key["kid"] == kid), None)

        if not key:
            raise Exception("Public key not found in JWKS list from Google.")

        # Verify the signature and claims
        decoded_token = jwt.decode(
            id_token,
            key,
            algorithms=[header.get("alg")],
            audience=client_id,
            issuer="https://accounts.google.com",
            access_token=access_token,
        )
        return decoded_token

    def _get_google_user_info(self, google_token: str) -> Dict[str, Any]:
        """
        Get user info from Google using an access token
        """
        try:
            response = requests.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {google_token}"},
            )

            if response.status_code == 200:
                return response.json()
            else:
                print(f"Google API error: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"Error fetching Google user info: {e}")
            return None

    def logout(self, refresh_token: str) -> Dict[str, Any]:
        """
        Revoke a refresh token to logout
        """
        try:
            # Find the refresh token in the database
            db_refresh_token = (
                self.db.query(RefreshToken).filter(RefreshToken.token == refresh_token).first()
            )

            if not db_refresh_token:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Token not found")

            # Revoke the token
            db_refresh_token.is_revoked = True
            self.db.commit()

            return {"message": "Successfully logged out"}

        except Exception as e:
            print(f"Error in logout: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to logout: {str(e)}",
            )

    def _generate_unique_refresh_token(self, user_id: str) -> str:
        """
        Generate a unique refresh token with a random suffix to ensure uniqueness
        """
        # Generate a random suffix (8 characters)
        suffix = "".join(random.choices(string.ascii_letters + string.digits, k=8))

        # Create a refresh token with the user ID and random suffix
        return create_refresh_token(subject=f"{user_id}:{suffix}")

    def generate_test_token(self, phone_region: str, phone_number: str) -> Optional[str]:
        """
        Generate a test Firebase ID token for a given phone number.
        This is for testing purposes only.
        """
        # Check if user exists in Firebase
        firebase_phone_number = f"{phone_region}{phone_number}"
        try:
            user = firebase_auth.get_user_by_phone_number(firebase_phone_number)
            print(f"Found existing Firebase user with phone: {firebase_phone_number}")
        except firebase_auth.UserNotFoundError:
            # Create user if not exists
            user = firebase_auth.create_user(phone_number=firebase_phone_number)
            print(f"Created new Firebase user with phone: {firebase_phone_number}")

        try:
            # Create custom token
            custom_token = firebase_auth.create_custom_token(user.uid)
            print(f"Created custom token for user: {user.uid}")

            # Exchange for ID token
            response = requests.post(
                f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithCustomToken?key={settings.FIREBASE_API_KEY}",
                json={"token": custom_token.decode("utf-8"), "returnSecureToken": True},
            )

            if response.status_code == 200:
                id_token = response.json().get("idToken")
                print("Successfully exchanged for ID token")
                return id_token
            else:
                print(f"Error exchanging token: {response.text}")
                return None
        except Exception as e:
            print(f"Error generating test token: {e}")
