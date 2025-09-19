from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from fastapi import status as http_status
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate

from app.core.dependencies import FlexUserDep, SessionDep
from app.schemas.match import MatchOut
from app.services.match_service import MatchService
from app.services.matching_cron_service import MatchingCronService

router = APIRouter()


@router.get(
    "/me",
    response_model=Page[MatchOut],
    openapi_extra={"security": [{"APIKeyHeader": [], "HTTPBearer": []}]},
)
def get_my_matches(
    session: SessionDep,
    current_user: FlexUserDep,
    status: str = Query(None, description="Filter by match status"),
) -> Page[MatchOut]:
    """
    Get all matches for the current authenticated user
    """
    match_service = MatchService(session)
    matches = match_service.get_user_matches(current_user.id, status)
    return paginate(matches)


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
    return match


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
    Accept a match belonging to the current user
    """
    match_service = MatchService(session)
    result = match_service.accept_match(match_id, current_user.id)
    return result


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
    return match


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
