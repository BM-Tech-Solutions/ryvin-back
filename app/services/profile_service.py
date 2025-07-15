import os
import uuid
from typing import List
from uuid import UUID

from fastapi import HTTPException, UploadFile, status

from app.models.photo import Photo
from app.models.user import User
from app.schemas.profile import ProfileCompletion
from app.schemas.user import UserUpdate

from .base_service import BaseService
from .user_service import UserService


class ProfileService(BaseService):
    """
    Service for profile-related operations
    """

    def get_profile(self, user_id: UUID) -> User:
        """
        Get user profile by ID
        """
        user_service = UserService(self.db)
        user = user_service.get_user_by_id(user_id)

        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        return user

    def update_profile(self, user: User, profile_data: UserUpdate) -> User:
        """
        Update user profile
        """
        user_service = UserService(self.db)
        return user_service.update_user(user, profile_data)

    def get_profile_photos(self, user_id: UUID) -> List[Photo]:
        """
        Get user profile photos
        """
        return self.db.query(Photo).filter(Photo.user_id == user_id).all()

    def upload_photo(self, user: User, file: UploadFile) -> Photo:
        """
        Upload a profile photo
        """
        # Check if user has reached photo limit
        photo_count = self.db.query(Photo).filter(Photo.user_id == user.id).count()
        if photo_count >= 6:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum number of photos (6) reached",
            )

        # Validate file type
        allowed_extensions = [".jpg", ".jpeg", ".png"]
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type not allowed. Allowed types: {', '.join(allowed_extensions)}",
            )

        # Generate unique filename
        filename = f"{uuid.uuid4()}{file_ext}"

        # In a real app, we would save the file to storage (S3, etc.)
        # For now, we'll just pretend we saved it
        file_path = f"uploads/photos/{filename}"

        # Create photo record
        photo = Photo(
            user_id=user.id,
            file_path=file_path,
            is_primary=photo_count == 0,  # First photo is primary
        )

        self.db.add(photo)
        self.db.commit()
        self.db.refresh(photo)

        return photo

    def delete_photo(self, user: User, photo_id: UUID) -> bool:
        """
        Delete a profile photo
        """
        photo = self.db.query(Photo).filter(Photo.id == photo_id, Photo.user_id == user.id).first()

        if not photo:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Photo not found")

        was_primary = photo.is_primary

        # In a real app, we would delete the file from storage

        # Delete photo record
        self.db.delete(photo)
        self.db.commit()

        # If deleted photo was primary, set another photo as primary
        if was_primary:
            next_photo = self.db.query(Photo).filter(Photo.user_id == user.id).first()
            if next_photo:
                next_photo.is_primary = True
                self.db.commit()

        return True

    def set_primary_photo(self, user: User, photo_id: UUID) -> Photo:
        """
        Set a photo as primary
        """
        photo = self.db.query(Photo).filter(Photo.id == photo_id, Photo.user_id == user.id).first()

        if not photo:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Photo not found")

        # Clear primary flag on all user photos
        self.db.query(Photo).filter(Photo.user_id == user.id).update({"is_primary": False})

        # Set new primary photo
        photo.is_primary = True
        self.db.commit()
        self.db.refresh(photo)

        return photo

    def get_profile_completion(self, user: User) -> ProfileCompletion:
        """
        Calculate profile completion percentage and missing fields
        """
        required_fields = [
            "first_name",
            "last_name",
            "birth_date",
            "gender",
            "bio",
            "location",
            "occupation",
        ]

        # Check if user has photos
        has_photos = self.db.query(Photo).filter(Photo.user_id == user.id).count() > 0

        # Check if user has completed questionnaire
        has_completed_questionnaire = user.has_completed_questionnaire

        # Count completed required fields
        completed_fields = 0
        missing_fields = []

        for field in required_fields:
            if getattr(user, field) is not None and getattr(user, field) != "":
                completed_fields += 1
            else:
                missing_fields.append(field)

        # Calculate completion percentage
        # Profile fields (60%), Photos (20%), Questionnaire (20%)
        profile_completion = (completed_fields / len(required_fields)) * 60
        photo_completion = 20 if has_photos else 0
        questionnaire_completion = 20 if has_completed_questionnaire else 0

        total_completion = int(profile_completion + photo_completion + questionnaire_completion)

        return ProfileCompletion(
            completion_percentage=total_completion,
            missing_profile_fields=missing_fields,
            has_photos=has_photos,
            has_completed_questionnaire=has_completed_questionnaire,
        )
