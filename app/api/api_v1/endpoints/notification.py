from uuid import UUID

from fastapi import APIRouter
from fastapi import status as http_status
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate

from app.core.dependencies import FlexUserDep, SessionDep
from app.schemas.notifications import NotificationOut, NotificationUpdate
from app.services.notification_service import NotificationService

router = APIRouter()


@router.get(
    "",
    status_code=http_status.HTTP_200_OK,
    response_model=Page[NotificationOut],
    openapi_extra={"security": [{"APIKeyHeader": [], "HTTPBearer": []}]},
)
def get_user_notifs(
    session: SessionDep, current_user: FlexUserDep, is_read: bool = None
) -> Page[NotificationOut]:
    """
    Get all matches for the current authenticated user
    """
    notif_service = NotificationService(session)
    notifs = notif_service.get_user_notifs(current_user.id, is_read)
    return paginate(notifs)


@router.get(
    "/{notif_id}",
    status_code=http_status.HTTP_200_OK,
    response_model=NotificationOut,
    openapi_extra={"security": [{"APIKeyHeader": [], "HTTPBearer": []}]},
)
def get_user_notif(
    session: SessionDep, current_user: FlexUserDep, notif_id: UUID
) -> NotificationOut:
    """
    Get a specific notification by ID (same user or admin)
    """
    notif_service = NotificationService(session)
    return notif_service.get_notification(current_user, notif_id)


@router.put(
    "/{notif_id}",
    status_code=http_status.HTTP_200_OK,
    response_model=NotificationOut,
    openapi_extra={"security": [{"APIKeyHeader": [], "HTTPBearer": []}]},
)
def update_notif(
    session: SessionDep, current_user: FlexUserDep, notif_id: UUID, notif_in: NotificationUpdate
) -> NotificationOut:
    """
    Update a notification by ID (same user or admin)
    """
    notif_service = NotificationService(session)
    notif = notif_service.get_notification(current_user, notif_id)
    notif = notif_service.update_notif(notif, notif_in)
    return notif


@router.delete(
    "/{notif_id}",
    status_code=http_status.HTTP_204_NO_CONTENT,
    openapi_extra={"security": [{"APIKeyHeader": [], "HTTPBearer": []}]},
)
def delete_notif(session: SessionDep, current_user: FlexUserDep, notif_id: UUID):
    """
    Delete a notification by ID (same user or admin)
    """
    notif_service = NotificationService(session)
    notif = notif_service.get_notification(current_user, notif_id)
    session.delete(notif)
    session.commit()
