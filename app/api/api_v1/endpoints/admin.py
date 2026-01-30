import json
from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, Security
from fastapi import status as http_status
from fastapi.requests import Request
from pydantic import BaseModel, EmailStr

from app.core.dependencies import AdminUserDep, SessionDep
from app.core.security import get_password_hash, utc_now
from app.core.utils import Page, paginate
from app.main import api_key_header
from app.models.enums import MatchStatus
from app.models.user import User
from app.schemas.journey import JourneyOut
from app.schemas.match import MatchOut
from app.schemas.user import UserOut
from app.services.admin_service import AdminService
from app.services.match_service import MatchService
from app.services.matching_cron_service import MatchingCronService
from app.services.user_service import UserService
from seed_questionnaires import (
    seed_questionnaires_from_db,
)

# Import seeding utilities
from seed_users import create_test_users

router = APIRouter()


class SeedAdminRequest(BaseModel):
    phone_region: str | None = None
    phone_number: str | None = None
    email: EmailStr
    password: str


@router.post("/seed-admin", status_code=http_status.HTTP_200_OK)
def seed_admin(
    session: SessionDep,
    request: SeedAdminRequest,
    api_key: str = Security(api_key_header),
) -> dict:
    """
    Create or promote a user to admin.
    - Protected by API-Token (master) via middleware and route Security.
    - Upserts by email or phone_number, sets is_admin and is_verified to True.
    """
    # Try find by email first
    user: User | None = None
    if request.email:
        user = session.query(User).filter(User.email == request.email).first()

    created = not user
    if not user:
        user = User(
            phone_region=request.phone_region,
            phone_number=request.phone_number,
            email=str(request.email) if request.email else None,
            password=get_password_hash(request.password),
        )
        session.add(user)
        session.flush()
    else:
        if "phone_region" in request.model_dump(exclude_unset=True):
            user.phone_region = request.phone_region
        if "phone_number" in request.model_dump(exclude_unset=True):
            user.phone_number = request.phone_number
        user.password = get_password_hash(request.password)

    # Promote to admin and verify
    user.is_active = True
    user.is_admin = True
    user.is_verified = True
    if not user.verified_at:
        user.verified_at = utc_now()

    session.commit()

    return {
        "message": "Admin created" if created else "Admin promoted",
        "user_id": str(user.id),
        "email": user.email,
        "phone_region": user.phone_region,
        "phone_number": user.phone_number,
        "is_admin": user.is_admin,
    }


class SeedUsersResponse(BaseModel):
    created_count: int
    users: list[dict]


@router.post("/seed-users", status_code=http_status.HTTP_200_OK, response_model=SeedUsersResponse)
def seed_users_endpoint(
    session: SessionDep,
    admin_user: AdminUserDep,
) -> SeedUsersResponse:
    """
    Seed 60 test users (30 male, 30 female).
    Also writes created_users.json for questionnaire seeding.
    """
    users = create_test_users(session) or []
    try:
        with open("created_users.json", "w", encoding="utf-8") as f:
            json.dump(users, f, ensure_ascii=False, indent=2, default=str)
    except Exception:
        # Non-fatal if file write fails; still return created users
        pass
    return SeedUsersResponse(created_count=len(users), users=users)


class SeedQuestionnairesResponse(BaseModel):
    success: bool
    mode: str


@router.post(
    "/seed-questionnaires",
    status_code=http_status.HTTP_200_OK,
    response_model=SeedQuestionnairesResponse,
)
def seed_questionnaires_endpoint(
    session: SessionDep,
    admin_user: AdminUserDep,
) -> SeedQuestionnairesResponse:
    """
    Seed questionnaires for users.
    """
    mode = "db"
    success = seed_questionnaires_from_db(session)
    return SeedQuestionnairesResponse(success=bool(success), mode=mode)


@router.post("/matching/trigger", status_code=http_status.HTTP_200_OK)
async def trigger_matching_all(
    session: SessionDep,
    admin_user: AdminUserDep,
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
    admin_user: AdminUserDep,
) -> dict:
    """Trigger matching for a specific user (admin)."""
    matching_service = MatchingCronService(session)
    result = await matching_service.process_new_user_matching(user_id)
    return {"message": "Matching process triggered for user", "result": result}


@router.get("/matches/{match_id}", response_model=MatchOut)
def admin_get_match_by_id(
    session: SessionDep,
    match_id: UUID,
    admin_user: AdminUserDep,
) -> MatchOut:
    """Get a specific match by ID (admin)."""
    match = MatchService(session).get_match_by_id(match_id)
    if not match:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Match not found")
    return MatchOut.from_match(match)


@router.get("/users/{user_id}/matches", response_model=Page[MatchOut])
def admin_get_user_matches(
    request: Request,
    session: SessionDep,
    admin_user: AdminUserDep,
    user_id: UUID,
    status: str | None = Query(None, description="Filter by match status"),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=25, ge=1, le=100),
) -> Page[MatchOut]:
    """Get matches for a given user (admin)."""
    matches = MatchService(session).get_user_matches(user_id, status)
    page = paginate(query=matches, page=page, per_page=per_page, request=request)
    page.items = [MatchOut.from_match(m) for m in page.items]
    return page


@router.get("/users", response_model=Page[UserOut])
def get_users(
    request: Request,
    session: SessionDep,
    admin_user: AdminUserDep,
    search: str | None = Query(None, description="Search Query"),
    is_active: bool | None = Query(None, description="Filter by active status"),
    is_deleted: bool | None = Query(None, description="Filter by deletion status"),
    is_verified: bool | None = Query(None, description="Filter by verification status"),
    requested_deletion: bool | None = Query(None, description="Filter by Request Deletion"),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=25, ge=1, le=100),
) -> Page[UserOut]:
    """
    Get all users (admin only)
    """
    users = AdminService(session).get_users(
        search=search,
        is_active=is_active,
        is_deleted=is_deleted,
        is_verified=is_verified,
        requested_deletion=requested_deletion,
    )
    return paginate(query=users, page=page, per_page=per_page, request=request)


@router.get("/users/{user_id}", response_model=Optional[UserOut])
def get_user(
    session: SessionDep,
    admin_user: AdminUserDep,
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
    admin_user: AdminUserDep,
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
def unban_user(session: SessionDep, admin_user: AdminUserDep, user_id: UUID):
    """
    Unban a user (admin only)
    """
    admin_service = AdminService(session)
    admin_service.unban_user(user_id)

    return {"message": "User unbanned successfully"}


@router.get("/users/{user_id}/deactivate", response_model=UserOut)
def deactivate_user(session: SessionDep, admin_user: AdminUserDep, user_id: UUID):
    """
    Deactivate a user account
    """
    user_service = UserService(session)
    user = user_service.get_user_or_404(user_id)
    return user_service.deactivate_user(user=user)


@router.get("/users/{user_id}/activate", response_model=UserOut)
def activate_user(session: SessionDep, admin_user: AdminUserDep, user_id: UUID):
    """
    Deactivate a user account
    """
    user_service = UserService(session)
    user = user_service.get_user_or_404(user_id)
    if user.is_deleted:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail="User Is Deleted")
    return user_service.reactivate_user(user=user)


@router.get("/users/{user_id}/delete")
def delete_user(session: SessionDep, admin_user: AdminUserDep, user_id: UUID):
    """
    Soft Delete a user and its related resources
    """
    user_service = UserService(session)
    user = user_service.get_user_or_404(user_id)
    return user_service.delete_user(user=user)


@router.get("/users/{user_id}/restore", response_model=UserOut)
def restore_user(session: SessionDep, admin_user: AdminUserDep, user_id: UUID):
    """
    Restore a soft deleted user and its related resources
    """
    user_service = UserService(session)
    user = user_service.get_user_or_404(user_id)
    return user_service.restore_user(user=user)


@router.get("/matches", response_model=Page[MatchOut])
def get_matches(
    request: Request,
    session: SessionDep,
    current_user: AdminUserDep,
    status: Optional[MatchStatus] = Query(None, description="Filter by match status"),
    min_compatibility: float = Query(
        None, ge=0, le=100, description="Filter by minimum compatibility score"
    ),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=25, ge=1, le=100),
) -> Page[MatchOut]:
    """
    Get all matches (admin only)
    """
    matches = AdminService(session).get_matches(status, min_compatibility)
    page = paginate(query=matches, page=page, per_page=per_page, request=request)
    page.items = [MatchOut.from_match(m) for m in page.items]
    return page


@router.get("/journeys", response_model=Page[JourneyOut])
def get_journeys(
    request: Request,
    session: SessionDep,
    current_user: AdminUserDep,
    current_step: int = Query(None, description="Filter by current step"),
    is_completed: bool = Query(None, description="Filter by completion status"),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=25, ge=1, le=100),
) -> Page[JourneyOut]:
    """
    Get all journeys (admin only)
    """
    journeys = AdminService(session).get_journeys(
        is_completed=is_completed, current_step=current_step
    )
    return paginate(query=journeys, page=page, per_page=per_page, request=request)


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
