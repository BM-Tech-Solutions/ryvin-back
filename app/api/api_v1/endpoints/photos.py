from typing import Any
from uuid import UUID

from fastapi import APIRouter, Query, UploadFile
from fastapi import status as http_status
from fastapi.requests import Request

from app.core.dependencies import SessionDep, VerifiedUserDep
from app.core.utils import Page, paginate
from app.schemas.photos import PhotoOut
from app.services.photo_service import PhotoService

router = APIRouter()


@router.get(
    "",
    status_code=http_status.HTTP_200_OK,
    response_model=Page[PhotoOut],
    openapi_extra={"security": [{"APIKeyHeader": [], "HTTPBearer": []}]},
)
def get_photos(
    request: Request,
    session: SessionDep,
    current_user: VerifiedUserDep,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=25, ge=1, le=100),
) -> Page[PhotoOut]:
    """
    get user's photos
    """
    photo_service = PhotoService(session)
    photos = photo_service.get_user_photos(current_user.id)
    return paginate(query=photos, page=page, per_page=per_page, request=request)


@router.post(
    "",
    status_code=http_status.HTTP_201_CREATED,
    openapi_extra={"security": [{"APIKeyHeader": [], "HTTPBearer": []}]},
)
async def upload_photo(
    session: SessionDep,
    current_user: VerifiedUserDep,
    file: UploadFile,
) -> PhotoOut:
    """
    Upload a user's photo
    """
    photo_service = PhotoService(session)
    photo = await photo_service.upload_photo(current_user.id, file)

    return photo


@router.post(
    "/set-primary/{photo_id}",
    status_code=http_status.HTTP_200_OK,
    openapi_extra={"security": [{"APIKeyHeader": [], "HTTPBearer": []}]},
)
def set_primary_photo(
    session: SessionDep,
    current_user: VerifiedUserDep,
    photo_id: UUID,
) -> PhotoOut:
    """
    Set a photo as primary for user
    """
    photo_service = PhotoService(session)
    photo = photo_service.set_primary_photo(current_user.id, photo_id)
    return photo


@router.delete(
    "/{photo_id}",
    status_code=http_status.HTTP_200_OK,
    openapi_extra={"security": [{"APIKeyHeader": [], "HTTPBearer": []}]},
)
def delete_photo(
    session: SessionDep,
    current_user: VerifiedUserDep,
    photo_id: UUID,
) -> Any:
    """
    Delete a user's photo
    """
    photo_service = PhotoService(session)
    photo_service.delete_photo(current_user.id, photo_id)

    return {"message": "Photo deleted successfully"}
