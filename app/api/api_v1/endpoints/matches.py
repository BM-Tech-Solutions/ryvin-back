from typing import Any, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_verified_user
from app.models.user import User
from app.models.enums import MatchStatus
from app.schemas.match import Match, MatchResponse
from app.services.match_service import MatchService

router = APIRouter()


@router.get("", response_model=List[Match])
def get_matches(
    status: str = Query(None, description="Filter by match status"),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get all matches for the current user
    """
    match_service = MatchService(db)
    matches = match_service.get_user_matches(current_user.id, status, skip, limit)
    return matches


@router.post("/discover", response_model=List[MatchResponse])
def discover_matches(
    limit: int = Query(10, ge=1, le=50, description="Number of potential matches to discover"),
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Discover potential matches for the current user
    """
    match_service = MatchService(db)
    potential_matches = match_service.discover_matches(current_user.id, limit)
    return potential_matches


@router.get("/{match_id}", response_model=Match)
def get_match(
    match_id: UUID,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get a specific match by ID
    """
    match_service = MatchService(db)
    match = match_service.get_match(match_id, current_user.id)
    return match


@router.post("/{match_id}/accept", status_code=status.HTTP_200_OK)
def accept_match(
    match_id: UUID,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Accept a match
    """
    match_service = MatchService(db)
    result = match_service.accept_match(match_id, current_user.id)
    return result


@router.post("/{match_id}/decline", status_code=status.HTTP_200_OK)
def decline_match(
    match_id: UUID,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Decline a match
    """
    match_service = MatchService(db)
    result = match_service.decline_match(match_id, current_user.id)
    return {"message": "Match declined successfully"}
