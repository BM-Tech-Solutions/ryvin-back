from typing import Any, List
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from fastapi import status as http_status

from app.core.dependencies import SessionDep
from app.schemas.match import Match
from app.services.match_service import MatchService
from app.services.matching_cron_service import MatchingCronService

router = APIRouter()


@router.get("", response_model=List[Match])
def get_all_matches(
    session: SessionDep,
    skip: int = Query(0, description="Number of matches to skip"),
    limit: int = Query(100, description="Maximum number of matches to return"),
) -> Any:
    """
    Get all existing matches in the system
    """
    match_service = MatchService(session)
    matches = match_service.get_all_matches(skip=skip, limit=limit)
    return matches


@router.get("/{user_id}", response_model=List[Match])
def get_user_matches(
    session: SessionDep,
    user_id: UUID,
    status: str = Query(None, description="Filter by match status"),
    skip: int = Query(0, description="Number of matches to skip"),
    limit: int = Query(100, description="Maximum number of matches to return"),
) -> Any:
    """
    Get all matches for a specific user
    """
    match_service = MatchService(session)
    matches = match_service.get_user_matches(user_id, status, skip, limit)
    return matches


@router.get("/match/{match_id}", response_model=Match)
def get_specific_match(session: SessionDep, match_id: UUID) -> Any:
    """
    Get a specific match by match ID
    """
    match_service = MatchService(session)
    match = match_service.get_match_by_id(match_id)
    if not match:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Match not found")
    return match


@router.post("/trigger-matching/{user_id}", status_code=http_status.HTTP_200_OK)
async def trigger_user_matching(session: SessionDep, user_id: UUID) -> Any:
    """
    Trigger matching algorithm for a specific user and return results
    """
    matching_service = MatchingCronService(session)

    # Run matching synchronously and return results
    result = await matching_service.process_new_user_matching(user_id)

    return {
        "message": f"Matching process completed for user {user_id}",
        "status": "completed",
        "results": result,
    }


@router.post("/admin/trigger-matching", status_code=http_status.HTTP_200_OK)
async def trigger_admin_matching(session: SessionDep, background_tasks: BackgroundTasks) -> Any:
    """
    Trigger matching algorithm for all users (admin function)
    """
    matching_service = MatchingCronService(session)

    # Run daily matching in background
    background_tasks.add_task(matching_service.run_daily_matching)

    return {"message": "Daily matching process triggered for all users", "status": "processing"}


@router.post("/match/{match_id}/accept", response_model=Match, status_code=http_status.HTTP_200_OK)
def accept_match(
    session: SessionDep,
    match_id: UUID,
    user_id: UUID = Query(..., description="User ID accepting the match"),
) -> Any:
    """
    Accept a match
    """
    match_service = MatchService(session)
    result = match_service.accept_match(match_id, user_id)
    return result


@router.post("/match/{match_id}/decline", response_model=Match, status_code=http_status.HTTP_200_OK)
def decline_match(
    session: SessionDep,
    match_id: UUID,
    user_id: UUID = Query(..., description="User ID declining the match"),
) -> Any:
    """
    Decline a match
    """
    match_service = MatchService(session)
    match = match_service.decline_match(match_id, user_id)
    return match
