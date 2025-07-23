from typing import Any
from uuid import UUID

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi import status as http_status

from app.core.dependencies import SessionDep, VerifiedUserDep
from app.schemas.photos import PhotoOut
from app.services.photo_service import PhotoService

router = APIRouter()


@router.get("", status_code=http_status.HTTP_201_CREATED)
def get_photos(
    session: SessionDep,
    current_user: VerifiedUserDep,
    skip: int = 0,
    limit: int = 100,
) -> list[PhotoOut]:
    """
    get user's photos
    """
    photo_service = PhotoService(session)
    photos = photo_service.get_user_photos(current_user.id, skip, limit)

    return photos


@router.post("", status_code=http_status.HTTP_201_CREATED)
def upload_photo(
    session: SessionDep,
    current_user: VerifiedUserDep,
    file: UploadFile = File(...),
) -> PhotoOut:
    """
    Upload a user's photo
    """
    photo_service = PhotoService(session)
    photo = photo_service.upload_photo(current_user.id, file)

    return photo


@router.post("/set-primary/{photo_id}", status_code=http_status.HTTP_200_OK)
def set_primary_photo(
    session: SessionDep,
    current_user: VerifiedUserDep,
    photo_id: UUID,
) -> Any:
    """
    Set a photo as primary for user
    """
    photo_service = PhotoService(session)
    photo = photo_service.set_primary_photo(current_user.id, photo_id)

    if not photo:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Photo not found",
        )

    return {"message": "Primary photo set successfully"}


@router.delete("/{photo_id}", status_code=http_status.HTTP_200_OK)
def delete_photo(
    session: SessionDep,
    current_user: VerifiedUserDep,
    photo_id: UUID,
) -> Any:
    """
    Delete a user's photo
    """
    photo_service = PhotoService(session)
    success = photo_service.delete_photo(current_user.id, photo_id)

    if not success:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Photo not found",
        )

    return {"message": "Photo deleted successfully"}
