from typing import Any, List, Optional
from uuid import UUID

from fastapi import APIRouter, Query
from fastapi import status as http_status

from app.core.dependencies import AdminUserDep, SessionDep
from app.schemas.journey import Journey
from app.schemas.match import Match
from app.schemas.user import UserOut
from app.services.admin_service import AdminService

router = APIRouter()


@router.get("/users", response_model=list[UserOut])
def get_users(
    session: SessionDep,
    current_user: AdminUserDep,
    search: str | None = Query(None, description="Search Query"),
    is_active: bool | None = Query(None, description="Filter by active status"),
    is_verified: bool | None = Query(None, description="Filter by verification status"),
    skip: int = 0,
    limit: int = 100,
) -> list[UserOut]:
    """
    Get all users (admin only)
    """
    users = AdminService(session).get_users(search, is_active, is_verified, skip, limit)
    return users


@router.get("/users/{user_id}", response_model=Optional[UserOut])
def get_user(
    session: SessionDep,
    current_user: AdminUserDep,
    user_id: UUID,
) -> Optional[UserOut]:
    """
    Get a specific user by ID (admin only)
    """
    admin_service = AdminService(session)
    user = admin_service.get_user_by_id(user_id)
    return user


@router.post("/users/{user_id}/ban", status_code=http_status.HTTP_200_OK)
def ban_user(
    session: SessionDep,
    current_user: AdminUserDep,
    user_id: UUID,
    reason: str,
) -> Any:
    """
    Ban a user (admin only)
    """
    admin_service = AdminService(session)
    admin_service.ban_user(user_id, reason)

    return {"message": "User banned successfully"}


@router.post("/users/{user_id}/unban", status_code=http_status.HTTP_200_OK)
def unban_user(
    session: SessionDep,
    current_user: AdminUserDep,
    user_id: UUID,
) -> Any:
    """
    Unban a user (admin only)
    """
    admin_service = AdminService(session)
    admin_service.unban_user(user_id)

    return {"message": "User unbanned successfully"}


@router.get("/matches/", response_model=List[Match])
def get_matches(
    session: SessionDep,
    current_user: AdminUserDep,
    status: str = Query(None, description="Filter by match status"),
    min_compatibility: float = Query(
        None, ge=0, le=100, description="Filter by minimum compatibility score"
    ),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Get all matches (admin only)
    """
    matches = AdminService(session).get_matches(status, skip, limit)
    return matches


@router.get("/journeys", response_model=List[Journey])
def get_journeys(
    session: SessionDep,
    current_user: AdminUserDep,
    current_step: int = Query(None, description="Filter by current step"),
    is_completed: bool = Query(None, description="Filter by completion status"),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Get all journeys (admin only)
    """
    journeys = AdminService(session).get_journeys(
        is_completed=is_completed, current_step=current_step, skip=skip, limit=limit
    )
    return journeys


@router.get("/stats", status_code=http_status.HTTP_200_OK)
def get_stats(session: SessionDep, current_user: AdminUserDep) -> Any:
    """
    Get system statistics (admin only)
    """
    stats = AdminService(session).get_system_stats()
    return stats


@router.post("/moderate/message/{message_id}", status_code=http_status.HTTP_200_OK)
def moderate_message(
    session: SessionDep,
    current_user: AdminUserDep,
    message_id: UUID,
    action: str,
    reason: str = None,
) -> Any:
    """
    Moderate a message (admin only)
    """
    admin_service = AdminService(session)
    admin_service.moderate_message(message_id, action, reason, current_user.id)

    return {"message": f"Message {action}d successfully"}


@router.post("/moderate/profile/{profile_id}", status_code=http_status.HTTP_200_OK)
def moderate_profile(
    session: SessionDep,
    current_user: AdminUserDep,
    profile_id: UUID,
    action: str,
    reason: str = None,
) -> Any:
    """
    Moderate a profile (admin only)
    """
    admin_service = AdminService(session)
    admin_service.moderate_profile(profile_id, action, reason, current_user.id)

    return {"message": f"Profile {action}ed successfully"}
