from typing import Any, List
from uuid import UUID

from fastapi import APIRouter, Query, status

from app.core.dependencies import AdminUserDep, SessionDep
from app.schemas.journey import Journey
from app.schemas.match import Match
from app.schemas.user import UserInDB
from app.services.admin_service import AdminService

router = APIRouter()


@router.get("/users", response_model=List[UserInDB])
def get_users(
    db: SessionDep,
    current_user: AdminUserDep,
    is_active: bool = Query(None, description="Filter by active status"),
    is_verified: bool = Query(None, description="Filter by verification status"),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Get all users (admin only)
    """
    users = AdminService(db).get_users(is_active, is_verified, skip, limit)
    return users


@router.get("/users/{user_id}", response_model=UserInDB)
def get_user(
    db: SessionDep,
    current_user: AdminUserDep,
    user_id: UUID,
) -> Any:
    """
    Get a specific user by ID (admin only)
    """
    admin_service = AdminService(db)
    user = admin_service.get_user(user_id)
    return user


@router.post("/users/{user_id}/ban", status_code=status.HTTP_200_OK)
def ban_user(
    db: SessionDep,
    current_user: AdminUserDep,
    user_id: UUID,
    reason: str,
) -> Any:
    """
    Ban a user (admin only)
    """
    admin_service = AdminService(db)
    admin_service.ban_user(user_id, current_user.id, reason)

    return {"message": "User banned successfully"}


@router.post("/users/{user_id}/unban", status_code=status.HTTP_200_OK)
def unban_user(
    db: SessionDep,
    current_user: AdminUserDep,
    user_id: UUID,
) -> Any:
    """
    Unban a user (admin only)
    """
    admin_service = AdminService(db)
    admin_service.unban_user(user_id)

    return {"message": "User unbanned successfully"}


@router.get("/matches", response_model=List[Match])
def get_matches(
    db: SessionDep,
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
    matches = AdminService(db).get_matches(status, min_compatibility, skip, limit)
    return matches


@router.get("/journeys", response_model=List[Journey])
def get_journeys(
    db: SessionDep,
    current_user: AdminUserDep,
    current_step: int = Query(None, description="Filter by current step"),
    is_completed: bool = Query(None, description="Filter by completion status"),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Get all journeys (admin only)
    """
    journeys = AdminService(db).get_journeys(current_step, is_completed, skip, limit)
    return journeys


@router.get("/stats", status_code=status.HTTP_200_OK)
def get_stats(db: SessionDep, current_user: AdminUserDep) -> Any:
    """
    Get system statistics (admin only)
    """
    stats = AdminService(db).get_stats()
    return stats


@router.post("/moderate/message/{message_id}", status_code=status.HTTP_200_OK)
def moderate_message(
    db: SessionDep,
    current_user: AdminUserDep,
    message_id: UUID,
    action: str,
    reason: str = None,
) -> Any:
    """
    Moderate a message (admin only)
    """
    admin_service = AdminService(db)
    admin_service.moderate_message(message_id, action, reason, current_user.id)

    return {"message": f"Message {action}d successfully"}


@router.post("/moderate/profile/{profile_id}", status_code=status.HTTP_200_OK)
def moderate_profile(
    db: SessionDep,
    current_user: AdminUserDep,
    profile_id: UUID,
    action: str,
    reason: str = None,
) -> Any:
    """
    Moderate a profile (admin only)
    """
    admin_service = AdminService(db)
    admin_service.moderate_profile(profile_id, action, reason, current_user.id)

    return {"message": f"Profile {action}ed successfully"}
