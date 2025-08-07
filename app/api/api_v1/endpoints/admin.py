from typing import Annotated, Any, List, Optional
from uuid import UUID

from fastapi import APIRouter, Body, HTTPException, Query
from fastapi import status as http_status
from sqlalchemy.exc import IntegrityError

from app.core.dependencies import AdminUserDep, SessionDep
from app.models.enums import MatchStatus
from app.models.user import User
from app.schemas.journey import JourneyCreate, JourneyOut
from app.schemas.match import MatchCreate, MatchOut
from app.schemas.user import TestUserCreate, UserOut
from app.services import AdminService, JourneyService, MatchService, UserService

router = APIRouter()


@router.get("/users", response_model=list[UserOut])
def get_users(
    session: SessionDep,
    current_user: AdminUserDep,
    search: str | None = Query(None, description="Search Query"),
    is_active: bool | None = Query(None, description="Filter by active status"),
    has_questionnaire: bool | None = Query(
        None, description="Filter by if user has a Questionnaire"
    ),
    is_verified: bool | None = Query(None, description="Filter by verification status"),
    skip: int = 0,
    limit: int = 100,
) -> list[UserOut]:
    """
    Get all users (admin only)
    """
    users = AdminService(session).get_users(
        search=search,
        is_active=is_active,
        is_verified=is_verified,
        has_questionnaire=has_questionnaire,
        skip=skip,
        limit=limit,
    )
    return users


@router.post("/users", response_model=UserOut)
def create_user(session: SessionDep, user_in: TestUserCreate) -> UserOut:
    """
    Create a new user (Admin only)
    """
    user = session.query(User).filter(User.phone_number == user_in.phone_number).first()
    if user:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=f"User with phone number: '{user_in.phone_number}' already exists",
        )
    try:
        user = User(**user_in.model_dump(exclude_unset=True))
        session.add(user)
        session.commit()
        session.refresh(user)
    except IntegrityError as e:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail={"args": e.args},
        )
    return user


@router.get("/users/{user_id}", response_model=Optional[UserOut])
def get_user(session: SessionDep, current_user: AdminUserDep, user_id: UUID) -> Optional[UserOut]:
    """
    Get a specific user by ID (admin only)
    """
    admin_service = AdminService(session)
    user = admin_service.get_user_by_id(user_id)
    return user


@router.put("/users/{user_id}/ban", response_model=UserOut)
def ban_user(
    session: SessionDep,
    current_user: AdminUserDep,
    user_id: UUID,
    reason: Annotated[str, Body(embed=True)],
) -> UserOut:
    """
    Ban a user (admin only)
    """
    admin_service = AdminService(session)
    return admin_service.ban_user(user_id, reason)


@router.put("/users/{user_id}/unban", response_model=UserOut)
def unban_user(session: SessionDep, current_user: AdminUserDep, user_id: UUID) -> UserOut:
    """
    Unban a user (admin only)
    """
    admin_service = AdminService(session)
    return admin_service.unban_user(user_id)


@router.get("/matches", response_model=List[MatchOut])
def get_matches(
    session: SessionDep,
    current_user: AdminUserDep,
    status: Optional[MatchStatus] = Query(None, description="Filter by match status"),
    min_compatibility: float = Query(
        None, ge=0, le=100, description="Filter by minimum compatibility score"
    ),
    skip: int = 0,
    limit: int = 100,
) -> List[MatchOut]:
    """
    Get all matches (admin only)
    """
    admin_service = AdminService(session)
    return admin_service.get_matches(status, min_compatibility, skip, limit)


@router.post("/matches", response_model=MatchOut)
def create_match(
    session: SessionDep, current_user: AdminUserDep, match_in: MatchCreate
) -> MatchOut:
    """
    Create a match between 2 users (for testing):
        - even if users didn't accept
        - even if users don't have a Questionnaire
    """
    user_service = UserService(session)
    user1 = user_service.get_user_by_id(match_in.user1_id)
    user2 = user_service.get_user_by_id(match_in.user2_id)
    if user1.id == user2.id:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=f"Can't create Match between same user: {user1} == {user2}",
        )
    match_service = MatchService(session)
    existing_match = match_service.get_match_by_users(
        match_in.user1_id, match_in.user2_id, raise_exc=False
    )
    if existing_match:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=f"There is already a Match between users: {user1} and {user2}",
        )

    new_match = match_service.create_match(match_in)
    return new_match


@router.get("/journeys", response_model=List[JourneyOut])
def get_journeys(
    session: SessionDep,
    current_user: AdminUserDep,
    current_step: int = Query(None, description="Filter by current step"),
    is_completed: bool = Query(None, description="Filter by completion status"),
    skip: int = 0,
    limit: int = 100,
) -> List[JourneyOut]:
    """
    Get all journeys (admin only)
    """
    admin_service = AdminService(session)
    return admin_service.get_journeys(
        is_completed=is_completed, current_step=current_step, skip=skip, limit=limit
    )


@router.post("/journeys", response_model=JourneyOut)
def create_journey(
    session: SessionDep,
    current_user: AdminUserDep,
    journey_in: JourneyCreate,
) -> JourneyOut:
    """
    Create a new Journey (Admin only)
    """
    journey_service = JourneyService(session)
    existing_journey = journey_service.get_journey_by_match(journey_in.match_id, raise_exc=False)
    if existing_journey:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=f"There is already a Journey linked to this match: {existing_journey}",
        )
    return journey_service.create_journey(journey_in)


@router.get("/stats", status_code=http_status.HTTP_200_OK)
def get_stats(session: SessionDep, current_user: AdminUserDep) -> Any:
    """
    Get system statistics (admin only)
    """
    stats = AdminService(session).get_system_stats()
    return stats


@router.post("/messages/{message_id}/moderate", status_code=http_status.HTTP_200_OK)
def moderate_message(
    session: SessionDep,
    current_user: AdminUserDep,
    message_id: UUID,
    action: str,
    reason: Annotated[str, Body(embed=True)] = None,
) -> Any:
    """
    Moderate a message (admin only)
    """
    admin_service = AdminService(session)
    admin_service.moderate_message(message_id, action, reason, current_user.id)

    return {"message": f"Message {action}d successfully"}
