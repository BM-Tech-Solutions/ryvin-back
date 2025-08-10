from typing import Annotated, List
from uuid import UUID

from fastapi import APIRouter, Body, Query
from fastapi import status as http_status

from app.core.dependencies import SessionDep, VerifiedUserDep
from app.schemas.journey import JourneyOut
from app.schemas.meeting import (
    MeetingFeedbackCreate,
    MeetingFeedbackOut,
    MeetingFeedbackUpdate,
    MeetingRequestCreate,
    MeetingRequestOut,
)
from app.schemas.message import MessageCreate, MessageOut
from app.services import JourneyService, MeetingService, MessageService

router = APIRouter()


# Journey
@router.get(
    "",
    response_model=List[JourneyOut],
    openapi_extra={"security": [{"APIKeyHeader": [], "BearerAuth": []}]},
)
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
    return journey_service.get_user_journeys(
        user_id=current_user.id,
        current_step=current_step,
        is_completed=is_completed,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/{journey_id}",
    response_model=JourneyOut,
    openapi_extra={"security": [{"APIKeyHeader": [], "BearerAuth": []}]},
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
    journey = journey_service.get_user_journey(current_user.id, journey_id)
    return journey


@router.post(
    "/{journey_id}/advance",
    status_code=http_status.HTTP_200_OK,
    openapi_extra={"security": [{"APIKeyHeader": [], "BearerAuth": []}]},
)
def advance_journey(
    session: SessionDep,
    current_user: VerifiedUserDep,
    journey_id: UUID,
) -> JourneyOut:
    """
    Advance to the next step in the journey
    """
    journey_service = JourneyService(session)
    journey = journey_service.get_user_journey(current_user.id, journey_id)
    return journey_service.advance_journey(journey)


@router.post(
    "/{journey_id}/end",
    status_code=http_status.HTTP_200_OK,
    openapi_extra={"security": [{"APIKeyHeader": [], "BearerAuth": []}]},
)
def end_journey(
    session: SessionDep,
    current_user: VerifiedUserDep,
    journey_id: UUID,
    reason: Annotated[str, Body(embed=True)],
) -> JourneyOut:
    """
    End the journey
    """
    journey_service = JourneyService(session)
    journey = journey_service.get_user_journey(current_user.id, journey_id)
    return journey_service.end_journey(journey, current_user.id, reason)


# Messages
@router.get(
    "/{journey_id}/messages",
    response_model=List[MessageOut],
    openapi_extra={"security": [{"APIKeyHeader": [], "BearerAuth": []}]},
)
def get_messages(
    session: SessionDep,
    current_user: VerifiedUserDep,
    journey_id: UUID,
    skip: int = 0,
    limit: int = 100,
) -> List[MessageOut]:
    """
    Get all messages for a journey
    """
    journey_service = JourneyService(session)
    journey = journey_service.get_user_journey(current_user.id, journey_id)
    message_service = MessageService(session)
    return message_service.get_journey_messages(journey.id, skip, limit)


@router.post(
    "/{journey_id}/messages",
    response_model=MessageOut,
    status_code=http_status.HTTP_201_CREATED,
    openapi_extra={"security": [{"APIKeyHeader": [], "BearerAuth": []}]},
)
def create_message(
    session: SessionDep,
    current_user: VerifiedUserDep,
    journey_id: UUID,
    message_in: MessageCreate,
) -> MessageOut:
    """
    Create a new message in a journey
    """

    journey_service = JourneyService(session)
    journey = journey_service.get_user_journey(current_user.id, journey_id)
    message_service = MessageService(session)
    return message_service.create_message(journey, current_user, message_in)


@router.delete(
    "/{journey_id}/messages/{message_id}",
    status_code=http_status.HTTP_204_NO_CONTENT,
    openapi_extra={"security": [{"APIKeyHeader": [], "BearerAuth": []}]},
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
    journey = journey_service.get_user_journey(current_user.id, journey_id)

    msg_service = MessageService(session)
    msg = msg_service.get_journey_message(journey.id, message_id)

    session.delete(msg)
    session.commit()


# Meeting Request
@router.get(
    "/{journey_id}/meeting-requests",
    response_model=List[MeetingRequestOut],
    openapi_extra={"security": [{"APIKeyHeader": [], "BearerAuth": []}]},
)
def get_meeting_requests(
    session: SessionDep,
    current_user: VerifiedUserDep,
    journey_id: UUID,
) -> List[MeetingRequestOut]:
    """
    Get all meeting requests for a journey
    """

    journey_service = JourneyService(session)
    journey = journey_service.get_user_journey(current_user.id, journey_id)

    meeting_service = MeetingService(session)
    return meeting_service.get_all_journey_meeting_reqs(journey.id)


@router.get("/{journey_id}/meeting-requests/{meeting_request_id}", response_model=MeetingRequestOut)
def get_meeting_request(
    session: SessionDep,
    current_user: VerifiedUserDep,
    journey_id: UUID,
    meeting_request_id: UUID,
) -> MeetingRequestOut:
    """
    Get one meeting request for a journey
    """

    journey_service = JourneyService(session)
    journey = journey_service.get_user_journey(current_user.id, journey_id)

    meeting_service = MeetingService(session)
    return meeting_service.get_journey_meeting_request(journey.id, meeting_request_id)


@router.post(
    "/{journey_id}/meeting-requests",
    response_model=MeetingRequestOut,
    status_code=http_status.HTTP_201_CREATED,
    openapi_extra={"security": [{"APIKeyHeader": [], "BearerAuth": []}]},
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

    journey_service = JourneyService(session)
    journey = journey_service.get_user_journey(current_user.id, journey_id)

    meeting_service = MeetingService(session)
    return meeting_service.create_meeting_request(journey, current_user, meeting_request_in)


@router.put(
    "/{journey_id}/meeting-requests/{meeting_request_id}/accept",
    status_code=http_status.HTTP_200_OK,
    openapi_extra={"security": [{"APIKeyHeader": [], "BearerAuth": []}]},
)
def accept_meeting_request(
    session: SessionDep,
    current_user: VerifiedUserDep,
    journey_id: UUID,
    meeting_request_id: UUID,
) -> MeetingRequestOut:
    """
    Accept a meeting request
    """

    journey_service = JourneyService(session)
    journey = journey_service.get_user_journey(current_user.id, journey_id)

    meeting_service = MeetingService(session)
    meeting_request = meeting_service.get_journey_meeting_request(journey.id, meeting_request_id)

    return meeting_service.accept_meeting_request(current_user, meeting_request)


@router.post(
    "/{journey_id}/meeting-requests/{meeting_request_id}/decline",
    status_code=http_status.HTTP_200_OK,
    openapi_extra={"security": [{"APIKeyHeader": [], "BearerAuth": []}]},
)
def decline_meeting_request(
    session: SessionDep,
    current_user: VerifiedUserDep,
    journey_id: UUID,
    meeting_request_id: UUID,
) -> MeetingRequestOut:
    """
    Decline a meeting request
    """

    journey_service = JourneyService(session)
    journey = journey_service.get_user_journey(current_user.id, journey_id)

    meeting_service = MeetingService(session)
    meeting_request = meeting_service.get_journey_meeting_request(journey.id, meeting_request_id)

    return meeting_service.decline_meeting_request(current_user, meeting_request)


@router.put(
    "/{journey_id}/meeting-requests/{meeting_request_id}/cancel",
    response_model=MeetingRequestOut,
)
def cancel_meeting_request(
    session: SessionDep,
    current_user: VerifiedUserDep,
    journey_id: UUID,
    meeting_request_id: UUID,
) -> MeetingRequestOut:
    """
    Cancel a meeting request
    """

    journey_service = JourneyService(session)
    journey = journey_service.get_user_journey(current_user.id, journey_id)

    meeting_service = MeetingService(session)
    meeting_request = meeting_service.get_journey_meeting_request(journey.id, meeting_request_id)

    return meeting_service.cancel_meeting_request(current_user, meeting_request)


# Meeting Feedback
@router.post(
    "/{journey_id}/meeting-requests/{meeting_request_id}/meeting-feedbacks",
    response_model=MeetingFeedbackOut,
    status_code=http_status.HTTP_201_CREATED,
    openapi_extra={"security": [{"APIKeyHeader": [], "BearerAuth": []}]},
)
def create_meeting_feedback(
    session: SessionDep,
    current_user: VerifiedUserDep,
    journey_id: UUID,
    meeting_request_id: UUID,
    feedback_in: MeetingFeedbackCreate,
) -> MeetingFeedbackOut:
    """
    Create feedback for a meeting
    """

    journey_service = JourneyService(session)
    journey = journey_service.get_user_journey(current_user.id, journey_id)

    meeting_service = MeetingService(session)
    meeting_request = meeting_service.get_journey_meeting_request(journey.id, meeting_request_id)
    return meeting_service.create_meeting_feedback(current_user.id, meeting_request.id, feedback_in)


@router.get(
    "/{journey_id}/meeting-requests/{meeting_request_id}/meeting-feedbacks",
    response_model=list[MeetingFeedbackOut],
)
def get_meeting_feedback(
    session: SessionDep,
    current_user: VerifiedUserDep,
    journey_id: UUID,
    meeting_request_id: UUID,
) -> list[MeetingFeedbackOut]:
    """
    Get feedback for a meeting
    """

    journey_service = JourneyService(session)
    journey = journey_service.get_user_journey(current_user.id, journey_id)

    meeting_service = MeetingService(session)
    meeting_request = meeting_service.get_journey_meeting_request(journey.id, meeting_request_id)
    return meeting_service.get_all_meeting_request_feedbacks(meeting_request.id)


@router.get(
    "/{journey_id}/meeting-requests/{meeting_request_id}/meeting-feedbacks/{meeting_feedback_id}",
    response_model=MeetingFeedbackOut,
)
def get_journey_meeting_feedback(
    session: SessionDep,
    current_user: VerifiedUserDep,
    journey_id: UUID,
    meeting_request_id: UUID,
    meeting_feedback_id: UUID,
) -> MeetingFeedbackOut:
    """
    Get feedback for a meeting
    """

    journey_service = JourneyService(session)
    journey = journey_service.get_user_journey(current_user.id, journey_id)

    meeting_service = MeetingService(session)
    meeting_request = meeting_service.get_journey_meeting_request(journey.id, meeting_request_id)
    return meeting_service.get_meeting_request_feedback(meeting_request.id, meeting_feedback_id)


@router.put(
    "/{journey_id}/meeting-requests/{meeting_request_id}/meeting-feedbacks/{meeting_feedback_id}",
    response_model=MeetingFeedbackOut,
)
def update_meeting_feedback(
    session: SessionDep,
    current_user: VerifiedUserDep,
    journey_id: UUID,
    meeting_request_id: UUID,
    meeting_feedback_id: UUID,
    feedback_in: MeetingFeedbackUpdate,
) -> MeetingFeedbackOut:
    """
    Update feedback for a meeting
    """

    journey_service = JourneyService(session)
    journey = journey_service.get_user_journey(current_user.id, journey_id)

    meeting_service = MeetingService(session)
    meeting_request = meeting_service.get_journey_meeting_request(journey.id, meeting_request_id)
    feedback = meeting_service.get_meeting_request_feedback(meeting_request.id, meeting_feedback_id)

    return meeting_service.update_meeting_feedback(feedback, feedback_in)
