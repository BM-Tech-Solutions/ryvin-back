from typing import Any
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from fastapi import status as http_status
from fastapi.requests import Request

from app.core.dependencies import FlexUserDep, SessionDep
from app.core.utils import Page, paginate
from app.models.user import User
from app.schemas.match import MatchCreateRequest, MatchOut
from app.services.match_service import MatchService
from app.services.matching_cron_service import MatchingCronService
from app.services.notification_service import new_match_notif_task

router = APIRouter()


@router.get(
    "/me",
    response_model=Page[MatchOut],
    openapi_extra={"security": [{"APIKeyHeader": [], "HTTPBearer": []}]},
)
def get_my_matches(
    request: Request,
    session: SessionDep,
    current_user: FlexUserDep,
    status: str = Query(None, description="Filter by match status"),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=25, ge=1, le=100),
) -> Page[MatchOut]:
    """
    Get all matches for the current authenticated user
    """
    match_service = MatchService(session)
    matches = match_service.get_user_matches(current_user.id, status)
    page = paginate(query=matches, page=page, per_page=per_page, request=request)
    page.items = [MatchOut.from_match(m) for m in page.items]
    return page


@router.get(
    "/{match_id}",
    response_model=MatchOut,
    openapi_extra={"security": [{"APIKeyHeader": [], "HTTPBearer": []}]},
)
def get_specific_match(session: SessionDep, current_user: FlexUserDep, match_id: UUID) -> MatchOut:
    """
    Get a specific match by match ID, only if it belongs to the current user
    """
    match_service = MatchService(session)
    match = match_service.get_match_by_id(match_id)
    if not match:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Match not found",
        )

    # Ownership check: user must be participant in the match
    if current_user.id not in [match.user1_id, match.user2_id]:
        raise HTTPException(status_code=http_status.HTTP_403_FORBIDDEN, detail="Forbidden")
    return MatchOut.from_match(match)


@router.post(
    "/{match_id}/accept",
    response_model=MatchOut,
    status_code=http_status.HTTP_200_OK,
    openapi_extra={"security": [{"APIKeyHeader": [], "HTTPBearer": []}]},
)
def accept_match(
    session: SessionDep,
    current_user: FlexUserDep,
    match_id: UUID,
) -> MatchOut:
    """
    Accept a match belonging to the current user.
    Returns the match details including journey_id if both users have accepted.
    """
    match_service = MatchService(session)
    result = match_service.accept_match(match_id, current_user.id)
    return MatchOut.from_match(result)


@router.post(
    "/{match_id}/decline",
    response_model=MatchOut,
    status_code=http_status.HTTP_200_OK,
    openapi_extra={"security": [{"APIKeyHeader": [], "HTTPBearer": []}]},
)
def decline_match(
    session: SessionDep,
    current_user: FlexUserDep,
    match_id: UUID,
) -> MatchOut:
    """
    Decline a match belonging to the current user
    """
    match_service = MatchService(session)
    match = match_service.decline_match(match_id, current_user.id)
    return MatchOut.from_match(match)


@router.post(
    "/create",
    response_model=MatchOut,
    status_code=http_status.HTTP_201_CREATED,
    openapi_extra={"security": [{"APIKeyHeader": [], "HTTPBearer": []}]},
)
def create_match_between_users(
    session: SessionDep,
    current_user: FlexUserDep,
    match_request: MatchCreateRequest,
    background_tasks: BackgroundTasks,
) -> MatchOut:
    """
    Create a match between two users by their IDs.
    This endpoint allows manual creation of matches, useful for admin purposes or testing.
    """
    # Validate that both users exist
    user1 = session.get(User, match_request.user1_id)
    user2 = session.get(User, match_request.user2_id)

    if not user1:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {match_request.user1_id} not found",
        )

    if not user2:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {match_request.user2_id} not found",
        )

    # Validate that users are different
    if match_request.user1_id == match_request.user2_id:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="Cannot create a match between the same user",
        )

    # Create the match using the service
    match_service = MatchService(session)
    try:
        match = match_service.create_match(
            match_request.user1_id,
            match_request.user2_id,
            match_request.compatibility_score,
        )
        background_tasks.add_task(new_match_notif_task, match_id=match.id)
        return MatchOut.from_match(match)
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create match: {str(e)}",
        )


@router.post(
    "/refresh",
    status_code=http_status.HTTP_200_OK,
    openapi_extra={"security": [{"APIKeyHeader": [], "HTTPBearer": []}]},
)
async def refresh_my_matches(
    session: SessionDep,
    current_user: FlexUserDep,
) -> Any:
    """
    Trigger matching algorithm for the current user and return results
    """
    matching_service = MatchingCronService(session)
    result = await matching_service.process_new_user_matching(current_user.id)
    return {
        "message": f"Matching process completed for user {current_user.id}",
        "status": "completed",
        "results": result,
    }
