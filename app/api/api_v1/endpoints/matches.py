from typing import Any, List
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from fastapi import status as http_status

from app.core.dependencies import SessionDep, VerifiedUserDep
from app.schemas.journey import JourneyCreate, JourneyOut
from app.schemas.match import MatchOut
from app.services.journey_service import JourneyService
from app.services.match_service import MatchService
from app.services.matching_cron_service import MatchingCronService

router = APIRouter()


@router.get("", response_model=List[MatchOut])
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


@router.get("/{user_id}", response_model=List[MatchOut])
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


@router.get("/{match_id}", response_model=MatchOut)
def get_match(session: SessionDep, current_user: VerifiedUserDep, match_id: UUID) -> MatchOut:
    """
    Get a specific match by match ID
    """
    match_service = MatchService(session)
    return match_service.get_user_match(current_user.id, match_id)


@router.get("/{match_id}/journey", response_model=JourneyOut)
def get_match_journey(
    session: SessionDep, current_user: VerifiedUserDep, match_id: UUID
) -> JourneyOut:
    """
    Get the Journey linked to this match
    """
    match_service = MatchService(session)
    journey_service = JourneyService(session)
    match_service.get_user_match(current_user.id, match_id)
    return journey_service.get_journey_by_match(match_id)


@router.post("/{match_id}/journey", response_model=JourneyOut)
def create_match_journey(
    session: SessionDep, current_user: VerifiedUserDep, match_id: UUID
) -> JourneyOut:
    """
    Create a Journey for this match
    """
    match_service = MatchService(session)
    journey_service = JourneyService(session)
    match = match_service.get_user_match(current_user.id, match_id)
    if match.journey:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="this Match already has a Journey",
        )
    return journey_service.create_journey(JourneyCreate(match_id=match_id))


@router.put("/{match_id}/accept", response_model=MatchOut)
def accept_match(session: SessionDep, current_user: VerifiedUserDep, match_id: UUID) -> MatchOut:
    """
    Accept a match
    """
    match_service = MatchService(session)
    match = match_service.get_user_match(current_user.id, match_id)
    return match_service.accept_match(match, current_user.id)


@router.put("/{match_id}/decline", response_model=MatchOut)
def decline_match(session: SessionDep, current_user: VerifiedUserDep, match_id: UUID) -> MatchOut:
    """
    Decline a match
    """
    match_service = MatchService(session)
    match = match_service.get_user_match(current_user.id, match_id)
    return match_service.decline_match(match, current_user.id)
