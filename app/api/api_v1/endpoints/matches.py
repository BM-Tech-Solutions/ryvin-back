from typing import Any, List
from uuid import UUID

from fastapi import APIRouter, Query
from fastapi import status as http_status

from app.core.dependencies import SessionDep, VerifiedUserDep
from app.schemas.match import Match, MatchResponse
from app.services.match_service import MatchService

router = APIRouter()


@router.get("", response_model=List[Match])
def get_matches(
    session: SessionDep,
    current_user: VerifiedUserDep,
    status: str = Query(None, description="Filter by match status"),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Get all matches for the current user
    """
    match_service = MatchService(session)
    matches = match_service.get_user_matches(current_user.id, status, skip, limit)
    return matches


@router.post("/discover", response_model=List[MatchResponse])
def discover_matches(
    session: SessionDep,
    current_user: VerifiedUserDep,
    limit: int = Query(10, ge=1, le=50, description="Number of potential matches to discover"),
) -> Any:
    """
    Discover potential matches for the current user
    """
    match_service = MatchService(session)
    potential_matches = match_service.discover_potential_matches(current_user.id, limit=limit)
    return potential_matches


@router.get("/{match_id}", response_model=Match)
def get_match(session: SessionDep, current_user: VerifiedUserDep, match_id: UUID) -> Any:
    """
    Get a specific match by ID
    """
    match_service = MatchService(session)
    match = match_service.get_match_by_id(match_id)
    return match


@router.post("/{match_id}/accept", status_code=http_status.HTTP_200_OK)
def accept_match(session: SessionDep, current_user: VerifiedUserDep, match_id: UUID) -> Any:
    """
    Accept a match
    """
    match_service = MatchService(session)
    result = match_service.accept_match(match_id, current_user.id)
    return result


@router.post("/{match_id}/decline", status_code=http_status.HTTP_200_OK)
def decline_match(session: SessionDep, current_user: VerifiedUserDep, match_id: UUID) -> Any:
    """
    Decline a match
    """
    match_service = MatchService(session)
    match = match_service.decline_match(match_id, current_user.id)
    return {"message": f"Match {match} declined successfully"}
