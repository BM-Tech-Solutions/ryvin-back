from typing import Any
from uuid import UUID

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.core.database import SessionDep
from app.core.dependencies import VerifiedUserDep
from app.schemas.profile import ProfileCompletion, ProfileCreate, ProfileOut, ProfileUpdate
from app.services.photo_service import PhotoService
from app.services.profile_service import ProfileService

router = APIRouter()


@router.get("/me")
def get_profile(
    db: SessionDep,
    current_user: VerifiedUserDep,
) -> ProfileOut:
    """
    Get current user's profile
    """
    profile = ProfileService(db).get_profile(current_user.id)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")

    return profile


@router.put("/me")
def update_profile(
    db: SessionDep,
    current_user: VerifiedUserDep,
    profile_in: ProfileUpdate,
) -> ProfileOut:
    """
    Update current user's profile
    """
    profile_service = ProfileService(db)
    profile = profile_service.get_profile(current_user.id)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    updated_profile = profile_service.update_profile(profile, profile_in)
    return updated_profile


@router.post("/me")
def create_profile(
    db: SessionDep,
    current_user: VerifiedUserDep,
    profile_in: ProfileCreate,
) -> ProfileOut:
    """
    create profile for current user
    """
    profile_service = ProfileService(db)
    profile = profile_service.get_profile(current_user.id)
    if profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="User already has a Profile"
        )
    new_profile = profile_service.create_profile(current_user.id, profile_in)
    return new_profile


@router.post("/photos", status_code=status.HTTP_201_CREATED)
def upload_photo(
    db: SessionDep,
    current_user: VerifiedUserDep,
    file: UploadFile = File(...),
) -> Any:
    """
    Upload a photo to user's profile
    """
    photo_service = PhotoService(db)
    photo = photo_service.upload_photo(current_user, file)

    return {
        "message": "Photo uploaded successfully",
        "photo_id": photo.id,
        "file_path": photo.file_path,
        "is_primary": photo.is_primary,
    }


@router.post("/photos/set-primary/{photo_id}", status_code=status.HTTP_200_OK)
def set_primary_photo(
    db: SessionDep,
    current_user: VerifiedUserDep,
    photo_id: UUID,
) -> Any:
    """
    Set a photo as primary for user's profile
    """
    photo_service = PhotoService(db)
    photo = photo_service.set_primary_photo(current_user.id, photo_id)

    if photo:
        return {"message": "Primary photo set successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Photo not found in profile",
        )


@router.delete("/photos/{photo_id}", status_code=status.HTTP_200_OK)
def delete_photo(
    db: SessionDep,
    current_user: VerifiedUserDep,
    photo_id: UUID,
) -> Any:
    """
    Delete a photo from user's profile
    """
    photo_service = PhotoService(db)
    success = photo_service.delete_photo(current_user.id, photo_id)

    if success:
        return {"message": "Photo deleted successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Photo not found in profile",
        )


@router.get("/completion-status", response_model=ProfileCompletion, status_code=status.HTTP_200_OK)
def get_profile_completion_status(
    db: SessionDep,
    current_user: VerifiedUserDep,
) -> Any:
    """
    Get profile completion status
    """
    profile_service = ProfileService(db)
    completion_info = profile_service.get_profile_completion(current_user.id)
    if not completion_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile or Questionnaire not found",
        )
    return completion_info
