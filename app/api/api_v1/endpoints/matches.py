from typing import List
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from fastapi import status as http_status

from app.core.dependencies import SessionDep, VerifiedUserDep
from app.models.enums import MatchStatus
from app.schemas.journey import JourneyCreate, JourneyOut
from app.schemas.match import MatchOut, PotentialMatch
from app.services.journey_service import JourneyService
from app.services.match_service import MatchService

router = APIRouter()


@router.get("", response_model=List[MatchOut])
def get_matches(
    session: SessionDep,
    current_user: VerifiedUserDep,
    status: MatchStatus = Query(None, description="Filter by match status"),
    has_journey: bool = None,
    skip: int = 0,
    limit: int = 100,
) -> List[MatchOut]:
    """
    Get all matches for the current user
    """
    match_service = MatchService(session)
    matches = match_service.get_user_matches(current_user.id, status, has_journey, skip, limit)
    return matches


@router.get("/discover", response_model=list[PotentialMatch])
def discover_matches(
    session: SessionDep,
    current_user: VerifiedUserDep,
    skip: int = 0,
    limit: int = Query(10, ge=1, le=50, description="Number of potential matches to discover"),
) -> list[PotentialMatch]:
    """
    Discover potential matches for the current user
    """
    match_service = MatchService(session)
    potential_matches = match_service.discover_potential_matches(current_user.id, skip, limit)
    return potential_matches


@router.get("/{match_id}", response_model=MatchOut)
def get_match(session: SessionDep, current_user: VerifiedUserDep, match_id: UUID) -> MatchOut:
    """
    Get a specific match by ID
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
