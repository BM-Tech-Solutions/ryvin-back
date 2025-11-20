from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from fastapi import status as http_status
from fastapi.requests import Request

from app.core.dependencies import SessionDep, VerifiedUserDep
from app.core.utils import Page, paginate
from app.models.enums import JourneyStep
from app.schemas.journey import JourneyOut
from app.schemas.meeting import (
    MeetingFeedbackCreate,
    MeetingFeedbackOut,
    MeetingRequestCreate,
    MeetingRequestOut,
)
from app.schemas.message import MessageOut
from app.schemas.photos import PhotoOut
from app.services import JourneyService, MeetingService, MessageService, PhotoService

router = APIRouter()


# Journey
@router.get(
    "",
    response_model=Page[JourneyOut],
    openapi_extra={"security": [{"APIKeyHeader": [], "HTTPBearer": []}]},
)
def get_journeys(
    request: Request,
    session: SessionDep,
    current_user: VerifiedUserDep,
    current_step: int = Query(None, description="Filter by current step"),
    is_completed: bool = Query(None, description="Filter by completion status"),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=25, ge=1, le=100),
) -> Page[JourneyOut]:
    """
    Get all journeys for the current user
    """
    journey_service = JourneyService(session)
    journeys = journey_service.get_journeys(
        user_id=current_user.id, current_step=current_step, is_completed=is_completed
    )
    return paginate(query=journeys, page=page, per_page=per_page, request=request)


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
) -> JourneyOut:
    """
    Advance to the next step in the journey
    """
    journey_service = JourneyService(session)
    journey = journey_service.advance_journey(current_user, journey_id)
    return journey


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
) -> JourneyOut:
    """
    End the journey
    """
    journey_service = JourneyService(session)
    journey = journey_service.end_journey(journey_id, current_user.id, reason)

    return journey


# Messages
@router.get(
    "/{journey_id}/messages",
    response_model=Page[MessageOut],
    openapi_extra={"security": [{"APIKeyHeader": [], "HTTPBearer": []}]},
)
def get_messages(
    request: Request,
    session: SessionDep,
    current_user: VerifiedUserDep,
    journey_id: UUID,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=25, ge=1, le=100),
) -> Page[MessageOut]:
    """
    Get all messages for a journey
    """
    message_service = MessageService(session)
    messages = message_service.get_messages(journey_id)
    return paginate(query=messages, page=page, per_page=per_page, request=request)


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
    response_model=Page[MeetingRequestOut],
    openapi_extra={"security": [{"APIKeyHeader": [], "HTTPBearer": []}]},
)
def get_meeting_requests(
    request: Request,
    session: SessionDep,
    current_user: VerifiedUserDep,
    journey_id: UUID,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=25, ge=1, le=100),
) -> Page[MeetingRequestOut]:
    """
    Get all meeting requests for a journey
    """
    meeting_service = MeetingService(session)
    meeting_requests = meeting_service.get_meeting_requests(journey_id)
    return paginate(query=meeting_requests, page=page, per_page=per_page, request=request)


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


# Photos
@router.get(
    "/{journey_id}/photos", openapi_extra={"security": [{"APIKeyHeader": [], "HTTPBearer": []}]}
)
def get_other_user_photos(
    request: Request,
    session: SessionDep,
    current_user: VerifiedUserDep,
    journey_id: UUID,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=25, ge=1, le=100),
) -> Page[PhotoOut]:
    """
    Get all Photos of the other user in this journey
    """
    journey_service = JourneyService(session)
    journey = journey_service.get_journey_by_id(journey_id)
    if not journey:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"Journey with ID '{journey_id}' not found",
        )

    if current_user.id not in [journey.match.user1_id, journey.match.user2_id]:
        raise HTTPException(
            status_code=http_status.HTTP_401_UNAUTHORIZED,
            detail="User not related to this journey",
        )

    if journey.current_step < JourneyStep.STEP2_PHOTOS_UNLOCKED:
        raise HTTPException(
            status_code=http_status.HTTP_401_UNAUTHORIZED,
            detail=f"Journey hasn't reached step '3' yet! (current step: '{journey.current_step}')",
        )

    other_user = journey.match.get_other_user(current_user.id)
    photo_service = PhotoService(session)
    photos = photo_service.get_user_photos(other_user.id)
    return paginate(photos, page=page, per_page=per_page, request=request)
