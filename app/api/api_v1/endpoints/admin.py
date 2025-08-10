from typing import Any, List, Optional
from uuid import UUID

from fastapi import APIRouter, Query, Security, HTTPException, BackgroundTasks
from fastapi import status as http_status
from pydantic import BaseModel, EmailStr

from app.core.dependencies import AdminViaTokenDep, SessionDep
from app.models.enums import MatchStatus
from app.schemas.journey import Journey
from app.schemas.match import Match
from app.schemas.user import UserOut
from app.services.admin_service import AdminService
from app.models.user import User
from app.core.security import utc_now
from app.main import api_key_header
from app.services.match_service import MatchService
from app.services.matching_cron_service import MatchingCronService

router = APIRouter()


class SeedAdminRequest(BaseModel):
    phone_number: str
    email: EmailStr | None = None


@router.post("/seed-admin", status_code=http_status.HTTP_200_OK)
def seed_admin(
    session: SessionDep,
    payload: SeedAdminRequest,
    api_key: str = Security(api_key_header),
) -> dict:
    """
    Create or promote a user to admin.
    - Protected by API-Token (master) via middleware and route Security.
    - Upserts by email or phone_number, sets is_admin and is_verified to True.
    """
    # Try find by email first, then by phone
    user: User | None = None
    if payload.email:
        user = session.query(User).filter(User.email == payload.email).first()
    if not user:
        user = session.query(User).filter(User.phone_number == payload.phone_number).first()

    created = False
    if not user:
        user = User(
            phone_number=payload.phone_number,
            email=str(payload.email) if payload.email else None,
            is_active=True,
            is_verified=True,
            verified_at=utc_now(),
        )
        session.add(user)
        session.flush()
        created = True

    # Promote to admin and verify
    user.is_admin = True
    user.is_verified = True
    if not user.verified_at:
        user.verified_at = utc_now()

    session.commit()

    return {
        "message": "Admin created" if created else "Admin promoted",
        "user_id": str(user.id),
        "email": user.email,
        "phone_number": user.phone_number,
        "is_admin": user.is_admin,
    }

@router.post("/matching/trigger", status_code=http_status.HTTP_200_OK)
async def trigger_matching_all(
    session: SessionDep,
    current_user: AdminViaTokenDep,
    background_tasks: BackgroundTasks,
) -> dict:
    """Trigger matching algorithm for all users (admin)."""
    matching_service = MatchingCronService(session)
    background_tasks.add_task(matching_service.run_daily_matching)
    return {"message": "Daily matching process triggered for all users", "status": "processing"}


@router.post("/matching/trigger/{user_id}", status_code=http_status.HTTP_200_OK)
async def trigger_matching_for_user(
    session: SessionDep,
    user_id: UUID,
    current_user: AdminViaTokenDep,
) -> dict:
    """Trigger matching for a specific user (admin)."""
    matching_service = MatchingCronService(session)
    result = await matching_service.process_new_user_matching(user_id)
    return {"message": "Matching process triggered for user", "result": result}


@router.get("/matches/{match_id}", response_model=Match)
def admin_get_match_by_id(
    session: SessionDep,
    match_id: UUID,
    current_user: AdminViaTokenDep,
) -> Match | None:
    """Get a specific match by ID (admin)."""
    match = MatchService(session).get_match_by_id(match_id)
    if not match:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Match not found")
    return match


@router.get("/users/{user_id}/matches", response_model=list[Match])
def admin_get_user_matches(
    session: SessionDep,
    current_user: AdminViaTokenDep,
    user_id: UUID,
    status: str | None = Query(None, description="Filter by match status"),
    skip: int = Query(0, description="Number of matches to skip"),
    limit: int = Query(100, description="Maximum number of matches to return"),
) -> list[Match]:
    """Get matches for a given user (admin)."""
    matches = MatchService(session).get_user_matches(user_id, status, skip, limit)
    return matches

@router.get("/users", response_model=list[UserOut])
def get_users(
    session: SessionDep,
    current_user: AdminViaTokenDep,
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
    current_user: AdminViaTokenDep,
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
    current_user: AdminViaTokenDep,
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
    current_user: AdminViaTokenDep,
    user_id: UUID,
) -> Any:
    """
    Unban a user (admin only)
    """
    admin_service = AdminService(session)
    admin_service.unban_user(user_id)

    return {"message": "User unbanned successfully"}


@router.get("/matches", response_model=List[Match])
def get_matches(
    session: SessionDep,
    current_user: AdminViaTokenDep,
    status: Optional[MatchStatus] = Query(None, description="Filter by match status"),
    min_compatibility: float = Query(
        None, ge=0, le=100, description="Filter by minimum compatibility score"
    ),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Get all matches (admin only)
    """
    matches = AdminService(session).get_matches(status, min_compatibility, skip, limit)
    return matches


@router.get("/journeys", response_model=List[Journey])
def get_journeys(
    session: SessionDep,
    current_user: AdminViaTokenDep,
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
def get_stats(session: SessionDep, current_user: AdminViaTokenDep) -> Any:
    """
    Get system statistics (admin only)
    """
    stats = AdminService(session).get_system_stats()
    return stats


@router.post("/moderate/message/{message_id}", status_code=http_status.HTTP_200_OK)
def moderate_message(
    session: SessionDep,
    current_user: AdminViaTokenDep,
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
