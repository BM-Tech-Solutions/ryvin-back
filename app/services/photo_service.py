import os
import uuid
from typing import Optional
from uuid import UUID

import aiofiles
from fastapi import HTTPException, UploadFile
from fastapi import status as http_status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import Photo

from .base_service import BaseService


class PhotoService(BaseService):
    """
    Service for User Photos operations
    """

    def __init__(self, db: Session):
        super().__init__(db)
        self.session = db

    def get_user_photos(self, user_id: UUID, skip: int = 0, limit: int = 100) -> list[Photo]:
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

    async def upload_photo(self, user_id: UUID, file: UploadFile) -> Photo:
        """
        Upload a photo
        """
        # Check if user has reached photo limit
        photo_count = self.session.query(Photo).filter(Photo.user_id == user_id).count()
        if photo_count >= settings.MAX_NBR_IMAGES:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=f"Maximum number of photos ({settings.MAX_NBR_IMAGES}) reached",
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
        file_path = f"media/photos/{filename}"
        file_abs_path = settings.BASE_DIR / file_path

        try:
            # make sure media/photos exists
            os.makedirs(file_abs_path.parent, exist_ok=True)

            # Open the destination file in binary write mode (async)
            async with aiofiles.open(file_abs_path, "wb") as dest_file:
                while chunk := await file.read(8192):
                    await dest_file.write(chunk)

        except Exception as e:
            raise HTTPException(
                status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"There was an error uploading the file: {e}",
            )
        finally:
            # Ensure the uploaded file's internal temporary file is closed
            file.file.close()

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
        if not photo:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=f"no photo with id={photo_id}",
            )
        if photo.user_id != user_id:
            raise HTTPException(
                status_code=http_status.HTTP_401_UNAUTHORIZED,
                detail=f"photo doesn't belong to user={user_id}",
            )

        was_primary = photo.is_primary

        try:
            os.remove(settings.BASE_DIR / photo.file_path)
        except FileNotFoundError:
            print(f"Error: File at {photo.file_path} not found.")

        # Delete photo record
        self.session.delete(photo)
        self.session.commit()

        # If deleted photo was primary, set another photo as primary
        if was_primary:
            next_photo = self.session.query(Photo).filter(Photo.user_id == user_id).first()
            if next_photo:
                next_photo.is_primary = True
                self.session.commit()

    def set_primary_photo(self, user_id: UUID, photo_id: UUID) -> Photo:
        """
        Set a photo as primary
        """
        photo = self.session.get(Photo, photo_id)
        if not photo:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=f"no photo with id={photo_id}",
            )
        if photo.user_id != user_id:
            raise HTTPException(
                status_code=http_status.HTTP_401_UNAUTHORIZED,
                detail=f"photo doesn't belong to user={user_id}",
            )

        # Clear primary flag on all user photos
        self.session.query(Photo).filter(Photo.user_id == user_id).update({"is_primary": False})

        # Set new primary photo
        photo.is_primary = True
        self.session.commit()
        self.session.refresh(photo)

        return photo
