from typing import Any, List
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_session
from app.core.dependencies import get_current_verified_user
from app.models.user import User
from app.schemas.journey import JourneyResponse
from app.schemas.meeting import (
    MeetingFeedback,
    MeetingFeedbackCreate,
    MeetingRequest,
    MeetingRequestCreate,
)
from app.schemas.message import MessageCreate, MessageResponse
from app.services import JourneyService, MeetingService, MessageService

router = APIRouter()


@router.get("", response_model=List[JourneyResponse])
def get_journeys(
    current_step: int = Query(None, description="Filter by current step"),
    is_completed: bool = Query(None, description="Filter by completion status"),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_session),
) -> Any:
    """
    Get all journeys for the current user
    """
    journey_service = JourneyService(db)
    journeys = journey_service.get_user_journeys(
        current_user.id, current_step, is_completed, skip, limit
    )
    return journeys


@router.get("/{journey_id}", response_model=JourneyResponse)
def get_journey(
    journey_id: UUID,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_session),
) -> Any:
    """
    Get a specific journey by ID
    """
    journey_service = JourneyService(db)
    journey = journey_service.get_journey(journey_id, current_user.id)
    return journey


@router.post("/{journey_id}/advance", status_code=status.HTTP_200_OK)
def advance_journey(
    journey_id: UUID,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_session),
) -> Any:
    """
    Advance to the next step in the journey
    """
    journey_service = JourneyService(db)
    journey = journey_service.advance_journey(journey_id, current_user.id)

    return {
        "message": f"Journey advanced to step {journey.current_step}",
        "current_step": journey.current_step,
        "journey": journey,
    }


@router.post("/{journey_id}/end", status_code=status.HTTP_200_OK)
def end_journey(
    journey_id: UUID,
    reason: str,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_session),
) -> Any:
    """
    End the journey
    """
    journey_service = JourneyService(db)
    journey_service.end_journey(journey_id, current_user.id, reason)

    return {"message": "Journey ended successfully"}


@router.get("/{journey_id}/messages", response_model=List[MessageResponse])
def get_messages(
    journey_id: UUID,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_session),
) -> Any:
    """
    Get all messages for a journey
    """
    message_service = MessageService(db)
    messages = message_service.get_messages(journey_id, current_user.id, skip, limit)
    return messages


@router.post(
    "/{journey_id}/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED
)
def create_message(
    journey_id: UUID,
    message_in: MessageCreate,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_session),
) -> Any:
    """
    Create a new message in a journey
    """
    message_service = MessageService(db)
    message = message_service.create_message(journey_id, current_user.id, message_in)
    return message


@router.post(
    "/{journey_id}/meeting-requests",
    response_model=MeetingRequest,
    status_code=status.HTTP_201_CREATED,
)
def create_meeting_request(
    journey_id: UUID,
    meeting_request_in: MeetingRequestCreate,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_session),
) -> Any:
    """
    Create a new meeting request in a journey
    """
    meeting_service = MeetingService(db)
    meeting_request = meeting_service.create_meeting_request(
        journey_id, current_user.id, meeting_request_in
    )
    return meeting_request


@router.get("/{journey_id}/meeting-requests", response_model=List[MeetingRequest])
def get_meeting_requests(
    journey_id: UUID,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_session),
) -> Any:
    """
    Get all meeting requests for a journey
    """
    meeting_service = MeetingService(db)
    meeting_requests = meeting_service.get_meeting_requests(journey_id, current_user.id)
    return meeting_requests


@router.post(
    "/{journey_id}/meeting-requests/{meeting_request_id}/accept", status_code=status.HTTP_200_OK
)
def accept_meeting_request(
    journey_id: UUID,
    meeting_request_id: UUID,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_session),
) -> Any:
    """
    Accept a meeting request
    """
    meeting_service = MeetingService(db)
    meeting_service.accept_meeting_request(journey_id, meeting_request_id, current_user.id)

    return {"message": "Meeting request accepted successfully"}


@router.post(
    "/{journey_id}/meeting-requests/{meeting_request_id}/decline", status_code=status.HTTP_200_OK
)
def decline_meeting_request(
    journey_id: UUID,
    meeting_request_id: UUID,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_session),
) -> Any:
    """
    Decline a meeting request
    """
    meeting_service = MeetingService(db)
    meeting_service.decline_meeting_request(journey_id, meeting_request_id, current_user.id)

    return {"message": "Meeting request declined successfully"}


@router.post(
    "/{journey_id}/meeting-feedback",
    response_model=MeetingFeedback,
    status_code=status.HTTP_201_CREATED,
)
def create_meeting_feedback(
    journey_id: UUID,
    feedback_in: MeetingFeedbackCreate,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_session),
) -> Any:
    """
    Create feedback for a meeting
    """
    meeting_service = MeetingService(db)
    feedback = meeting_service.create_meeting_feedback(journey_id, current_user.id, feedback_in)
    return feedback
