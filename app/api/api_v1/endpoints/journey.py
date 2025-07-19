from typing import Any, List, Optional
from uuid import UUID

from fastapi import APIRouter, Query
from fastapi import status as http_status

from app.core.dependencies import SessionDep, VerifiedUserDep
from app.schemas.journey import JourneyOut
from app.schemas.meeting import (
    MeetingFeedback,
    MeetingFeedbackCreate,
    MeetingRequestCreate,
    MeetingRequestOut,
)
from app.schemas.message import MessageCreate, MessageResponse
from app.services import JourneyService, MeetingService, MessageService

router = APIRouter()


@router.get("", response_model=List[JourneyOut])
def get_journeys(
    session: SessionDep,
    current_user: VerifiedUserDep,
    current_step: int = Query(None, description="Filter by current step"),
    is_completed: bool = Query(None, description="Filter by completion status"),
    skip: int = 0,
    limit: int = 100,
) -> List[JourneyOut]:
    """
    Get all journeys for the current user
    """
    journey_service = JourneyService(session)
    journeys = journey_service.get_journeys(
        user_id=current_user.id,
        current_step=current_step,
        is_completed=is_completed,
        skip=skip,
        limit=limit,
    )
    return journeys


@router.get("/{journey_id}", response_model=JourneyOut)
def get_journey(
    session: SessionDep,
    current_user: VerifiedUserDep,
    journey_id: UUID,
) -> Optional[JourneyOut]:
    """
    Get a specific journey by ID
    """
    journey_service = JourneyService(session)
    journey = journey_service.get_journey_by_id(journey_id)
    return journey


@router.post("/{journey_id}/advance", status_code=http_status.HTTP_200_OK)
def advance_journey(
    session: SessionDep,
    current_user: VerifiedUserDep,
    journey_id: UUID,
) -> Any:
    """
    Advance to the next step in the journey
    """
    journey_service = JourneyService(session)
    journey = journey_service.advance_journey(journey_id)

    return {
        "message": f"Journey advanced to step {journey.current_step}",
        "current_step": journey.current_step,
        "journey": journey,
    }


@router.post("/{journey_id}/end", status_code=http_status.HTTP_200_OK)
def end_journey(
    session: SessionDep,
    current_user: VerifiedUserDep,
    journey_id: UUID,
    reason: str,
) -> Any:
    """
    End the journey
    """
    journey_service = JourneyService(session)
    journey_service.end_journey(journey_id, current_user.id, reason)

    return {"message": "Journey ended successfully"}


@router.get("/{journey_id}/messages", response_model=List[MessageResponse])
def get_messages(
    session: SessionDep,
    current_user: VerifiedUserDep,
    journey_id: UUID,
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Get all messages for a journey
    """
    message_service = MessageService(session)
    messages = message_service.get_messages(journey_id, current_user.id, skip, limit)
    return messages


@router.post(
    "/{journey_id}/messages",
    response_model=MessageResponse,
    status_code=http_status.HTTP_201_CREATED,
)
def create_message(
    session: SessionDep,
    current_user: VerifiedUserDep,
    journey_id: UUID,
    message_in: MessageCreate,
) -> Any:
    """
    Create a new message in a journey
    """
    message_service = MessageService(session)
    message = message_service.create_message(journey_id, current_user.id, message_in)
    return message


@router.get("/{journey_id}/meeting-requests", response_model=List[MeetingRequestOut])
def get_meeting_requests(
    session: SessionDep,
    current_user: VerifiedUserDep,
    journey_id: UUID,
) -> List[MeetingRequestOut]:
    """
    Get all meeting requests for a journey
    """
    meeting_service = MeetingService(session)
    meeting_requests = meeting_service.get_meeting_requests(journey_id, current_user.id)
    return meeting_requests


@router.post(
    "/{journey_id}/meeting-requests",
    response_model=MeetingRequestOut,
    status_code=http_status.HTTP_201_CREATED,
)
def create_meeting_request(
    session: SessionDep,
    current_user: VerifiedUserDep,
    journey_id: UUID,
    meeting_request_in: MeetingRequestCreate,
) -> MeetingRequestOut:
    """
    Create a new meeting request in a journey
    """
    meeting_service = MeetingService(session)
    meeting_request = meeting_service.create_meeting_request(
        journey_id, current_user.id, meeting_request_in
    )
    return meeting_request


@router.post(
    "/{journey_id}/meeting-requests/{meeting_request_id}/accept",
    status_code=http_status.HTTP_200_OK,
)
def accept_meeting_request(
    session: SessionDep,
    current_user: VerifiedUserDep,
    journey_id: UUID,
    meeting_request_id: UUID,
) -> Any:
    """
    Accept a meeting request
    """
    meeting_service = MeetingService(session)
    meeting_service.accept_meeting_request(journey_id, meeting_request_id, current_user.id)

    return {"message": "Meeting request accepted successfully"}


@router.post(
    "/{journey_id}/meeting-requests/{meeting_request_id}/decline",
    status_code=http_status.HTTP_200_OK,
)
def decline_meeting_request(
    session: SessionDep,
    current_user: VerifiedUserDep,
    journey_id: UUID,
    meeting_request_id: UUID,
) -> Any:
    """
    Decline a meeting request
    """
    meeting_service = MeetingService(session)
    meeting_service.decline_meeting_request(journey_id, meeting_request_id, current_user.id)

    return {"message": "Meeting request declined successfully"}


@router.post(
    "/{journey_id}/meeting-feedback",
    response_model=MeetingFeedback,
    status_code=http_status.HTTP_201_CREATED,
)
def create_meeting_feedback(
    session: SessionDep,
    current_user: VerifiedUserDep,
    journey_id: UUID,
    feedback_in: MeetingFeedbackCreate,
) -> Any:
    """
    Create feedback for a meeting
    """
    meeting_service = MeetingService(session)
    feedback = meeting_service.create_meeting_feedback(journey_id, current_user.id, feedback_in)
    return feedback
