import os
import uuid
from typing import List, Optional
from uuid import UUID

from fastapi import HTTPException, UploadFile
from fastapi import status as http_status
from sqlalchemy.orm import Session

from app.models import Photo

from .base_service import BaseService


class PhotoService(BaseService):
    """
    Service for User Photos operations
    """

    def __init__(self, db: Session):
        super().__init__(db)
        self.session = db

    def get_user_photos(self, user_id: UUID, skip: int = 0, limit: int = 100) -> List[Photo]:
        """
        Get user photos
        """
        return (
            self.session.query(Photo)
            .filter(Photo.user_id == user_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_user_primary_photo(self, user_id: UUID) -> Optional[Photo]:
        """
        Get user primary photo
        """
        return (
            self.session.query(Photo)
            .filter(Photo.user_id == user_id, Photo.is_primary.is_(True))
            .first()
        )

    def upload_photo(self, user_id: UUID, file: UploadFile) -> Photo:
        """
        Upload a photo
        """
        # Check if user has reached photo limit
        photo_count = self.session.query(Photo).filter(Photo.user_id == user_id).count()
        if photo_count >= 6:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="Maximum number of photos (6) reached",
            )

        # Validate file type
        allowed_extensions = [".jpg", ".jpeg", ".png"]
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=f"File type not allowed. Allowed types: {', '.join(allowed_extensions)}",
            )

        # Generate unique filename
        filename = f"{uuid.uuid4()}{file_ext}"

        # In a real app, we would save the file to storage (S3, etc.)
        # For now, we'll just pretend we saved it
        file_path = f"uploads/photos/{filename}"

        # Create photo record
        photo = Photo(
            user_id=user_id,
            file_path=file_path,
            is_primary=photo_count == 0,  # First photo is primary
        )

        self.session.add(photo)
        self.session.commit()
        self.session.refresh(photo)

        return photo

    def delete_photo(self, user_id: UUID, photo_id: UUID) -> bool:
        """
        Delete a photo
        """
        photo = self.session.get(Photo, photo_id)
        if not photo or photo.user_id != user_id:
            return False

        was_primary = photo.is_primary

        # In a real app, we would delete the file from storage

        # Delete photo record
        self.session.delete(photo)
        self.session.commit()

        # If deleted photo was primary, set another photo as primary
        if was_primary:
            next_photo = self.session.query(Photo).filter(Photo.user_id == user_id).first()
            if next_photo:
                next_photo.is_primary = True
                self.session.commit()

        return True

    def set_primary_photo(self, user_id: UUID, photo_id: UUID) -> Optional[Photo]:
        """
        Set a photo as primary
        """
        photo = self.session.get(Photo, photo_id)
        if not photo or photo.user_id != user_id:
            return None

        # Clear primary flag on all user photos
        self.session.query(Photo).filter(Photo.user_id == user_id).update({"is_primary": False})

        # Set new primary photo
        photo.is_primary = True
        self.session.commit()
        self.session.refresh(photo)

        return photo
