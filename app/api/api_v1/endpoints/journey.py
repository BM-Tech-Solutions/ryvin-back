from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from fastapi import status as http_status

from app.core.dependencies import SessionDep, VerifiedUserDep
from app.schemas.journey import JourneyOut
from app.schemas.meeting import (
    MeetingFeedbackCreate,
    MeetingFeedbackOut,
    MeetingRequestCreate,
    MeetingRequestOut,
)
from app.schemas.message import MessageOut
from app.services import JourneyService, MeetingService, MessageService

router = APIRouter()


# Journey
@router.get(
    "",
    response_model=list[JourneyOut],
    openapi_extra={"security": [{"APIKeyHeader": [], "HTTPBearer": []}]},
)
def get_journeys(
    session: SessionDep,
    current_user: VerifiedUserDep,
    current_step: int = Query(None, description="Filter by current step"),
    is_completed: bool = Query(None, description="Filter by completion status"),
    skip: int = 0,
    limit: int = 100,
) -> list[JourneyOut]:
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


@router.get(
    "/{journey_id}",
    response_model=JourneyOut,
    openapi_extra={"security": [{"APIKeyHeader": [], "HTTPBearer": []}]},
)
def get_journey(
    session: SessionDep,
    current_user: VerifiedUserDep,
    journey_id: UUID,
) -> JourneyOut:
    """
    Get a specific journey by ID
    """
    journey_service = JourneyService(session)
    journey = journey_service.get_journey_by_id(journey_id)
    if not journey:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"Journey with ID '{journey_id}' not found",
        )
    return journey


@router.post(
    "/{journey_id}/advance",
    status_code=http_status.HTTP_200_OK,
    openapi_extra={"security": [{"APIKeyHeader": [], "HTTPBearer": []}]},
)
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


@router.post(
    "/{journey_id}/end",
    status_code=http_status.HTTP_200_OK,
    openapi_extra={"security": [{"APIKeyHeader": [], "HTTPBearer": []}]},
)
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


# Messages
@router.get(
    "/{journey_id}/messages",
    response_model=list[MessageOut],
    openapi_extra={"security": [{"APIKeyHeader": [], "HTTPBearer": []}]},
)
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
    messages = message_service.get_messages(journey_id, skip, limit)
    return messages


@router.delete(
    "/{journey_id}/messages/{message_id}",
    status_code=http_status.HTTP_204_NO_CONTENT,
    openapi_extra={"security": [{"APIKeyHeader": [], "HTTPBearer": []}]},
)
def delete_message(
    session: SessionDep,
    current_user: VerifiedUserDep,
    journey_id: UUID,
    message_id: UUID,
) -> None:
    """
    Delete a msg from a Journey
    """

    journey_service = JourneyService(session)
    journey = journey_service.get_journey_by_id(journey_id)
    if not journey:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Journey with not found",
        )

    if current_user.id not in [journey.match.user1_id, journey.match.user2_id]:
        raise HTTPException(
            status_code=http_status.HTTP_401_UNAUTHORIZED,
            detail="User not related to this journey",
        )

    msg_service = MessageService(session)
    msg = msg_service.get_journey_message(journey_id, message_id)
    if not msg:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Message with not found",
        )

    session.delete(msg)
    session.commit()


# Meeting Request
@router.get(
    "/{journey_id}/meeting-requests",
    response_model=list[MeetingRequestOut],
    openapi_extra={"security": [{"APIKeyHeader": [], "HTTPBearer": []}]},
)
def get_meeting_requests(
    session: SessionDep,
    current_user: VerifiedUserDep,
    journey_id: UUID,
) -> list[MeetingRequestOut]:
    """
    Get all meeting requests for a journey
    """
    meeting_service = MeetingService(session)
    meeting_requests = meeting_service.get_meeting_requests(journey_id)
    return meeting_requests


@router.post(
    "/{journey_id}/meeting-requests",
    response_model=MeetingRequestOut,
    status_code=http_status.HTTP_201_CREATED,
    openapi_extra={"security": [{"APIKeyHeader": [], "HTTPBearer": []}]},
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
    openapi_extra={"security": [{"APIKeyHeader": [], "HTTPBearer": []}]},
)
def accept_meeting_request(
    session: SessionDep,
    current_user: VerifiedUserDep,
    journey_id: UUID,
    meeting_request_id: UUID,
) -> Any:
    """
    Accept a meeting request (not implemented yet)
    """
    # meeting_service = MeetingService(session)
    # meeting_service.accept_meeting_request(journey_id, meeting_request_id, current_user.id)

    return {"message": "not implemented yet"}


@router.post(
    "/{journey_id}/meeting-requests/{meeting_request_id}/decline",
    status_code=http_status.HTTP_200_OK,
    openapi_extra={"security": [{"APIKeyHeader": [], "HTTPBearer": []}]},
)
def decline_meeting_request(
    session: SessionDep,
    current_user: VerifiedUserDep,
    journey_id: UUID,
    meeting_request_id: UUID,
) -> Any:
    """
    Decline a meeting request (not implemented yet)
    """
    # meeting_service = MeetingService(session)
    # meeting_service.decline_meeting_request(journey_id, meeting_request_id, current_user.id)

    return {"message": "not implemented yet"}


# Meeting Feedback
@router.post(
    "/{journey_id}/meeting-feedback",
    response_model=MeetingFeedbackOut,
    status_code=http_status.HTTP_201_CREATED,
    openapi_extra={"security": [{"APIKeyHeader": [], "HTTPBearer": []}]},
)
def create_meeting_feedback(
    session: SessionDep,
    current_user: VerifiedUserDep,
    journey_id: UUID,
    feedback_in: MeetingFeedbackCreate,
) -> MeetingFeedbackOut:
    """
    Create feedback for a meeting
    """
    journey_service = JourneyService(session)
    journey = journey_service.get_journey_by_id(journey_id)
    if not journey:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"Journey with ID '{journey_id}' not found",
        )
    if current_user.id not in [journey.match.user1, journey.match.user2]:
        raise HTTPException(
            status_code=http_status.HTTP_401_UNAUTHORIZED,
            detail=f"User doesn't belong to Journey with ID '{journey_id}'",
        )

    meeting_service = MeetingService(session)
    meeting_request = meeting_service.get_meeting_request_by_id(feedback_in.meeting_request_id)
    if not meeting_request:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"Meeting Request with ID '{feedback_in.meeting_request_id}' not found",
        )
    if not meeting_request.journey_id != journey_id:
        raise HTTPException(
            status_code=http_status.HTTP_401_UNAUTHORIZED,
            detail="Meeting Request doesn't belong to this journey",
        )

    feedback = meeting_service.create_meeting_feedback(current_user.id, feedback_in)
    return feedback
