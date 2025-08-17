from uuid import UUID

from fastapi import APIRouter, HTTPException, Request
from fastapi import status as http_status
from pydantic import BaseModel

from app.core.config import settings
from app.core.dependencies import FlexUserDep, SessionDep
from app.models.enums import TwilioEvent
from app.services.journey_service import JourneyService, MessageService
from app.services.twilio_service import TwilioService

router = APIRouter()


class TwilioChatTokenSchema(BaseModel):
    user_id: str
    chat_token: str


class TwilioCallTokenSchema(BaseModel):
    user_id: str
    call_token: str


class StartCallSchema(BaseModel):
    message: str = "Call successfully initiated."
    room_name: str


@router.post("/chat-webhook", openapi_extra={"security": []})
async def twilio_chat_webhook(request: Request, session: SessionDep):
    # Twilio sends data as application/x-www-form-urlencoded
    body = await request.form()
    body = dict(body)
    print("Twilio Chat Webhook:")
    print(f"\t{body = }")
    try:
        msg_service = MessageService(session)
        if body.get("EventType") == TwilioEvent.ON_MESSAGE_ADDED:
            msg_service.create_message(body)
        if body.get("EventType") == TwilioEvent.ON_MESSAGE_UPDATED:
            msg_service.update_message(body)
        if body.get("EventType") == TwilioEvent.ON_MESSAGE_REMOVED:
            msg_service.delete_message(body)

    except Exception as e:
        print(f"Error Handling Webhook {body.get('EventType')}: {e}")

    return {}


@router.post("/video-webhook", openapi_extra={"security": []})
async def twilio_video_webhook(request: Request):
    # Twilio sends data as application/x-www-form-urlencoded
    body = await request.form()
    body = dict(body)
    print("Twilio Video Webhook:")
    print(f"\t{body = }")
    return {}


@router.get(
    "/chat-token",
    openapi_extra={"security": [{"APIKeyHeader": [], "HTTPBearer": []}]},
    response_model=TwilioChatTokenSchema,
)
async def get_twilio_chat_token(current_user: FlexUserDep) -> TwilioChatTokenSchema:
    # Create the access token
    twilio_service = TwilioService()
    token = twilio_service.get_chat_token(user_id=str(current_user.id))

    return {"user_id": str(current_user.id), "chat_token": token}


@router.get(
    "/{journey_id}/call-token",
    openapi_extra={"security": [{"APIKeyHeader": [], "HTTPBearer": []}]},
    response_model=TwilioCallTokenSchema,
)
async def get_twilio_call_token(
    session: SessionDep,
    current_user: FlexUserDep,
    journey_id: UUID,
) -> TwilioCallTokenSchema:
    # video_room.unique_name == journey_id == conversation.unique_name
    room_name = str(journey_id)
    journey_service = JourneyService(session)
    journey = journey_service.get_journey_by_id(journey_id)
    if not journey:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"Journey with with id={journey_id} not found",
        )

    if current_user.id not in [journey.match.user1_id, journey.match.user2_id]:
        raise HTTPException(
            status_code=http_status.HTTP_401_UNAUTHORIZED,
            detail="User not related to this journey",
        )

    # Create the access token
    twilio_service = TwilioService()
    token = twilio_service.get_call_token(user_id=str(current_user.id), room_name=room_name)

    return {"user_id": str(current_user.id), "call_token": token}


@router.get(
    "/{journey_id}/start-call",
    openapi_extra={"security": [{"APIKeyHeader": [], "HTTPBearer": []}]},
    response_model=StartCallSchema,
)
async def start_call(
    session: SessionDep,
    current_user: FlexUserDep,
    journey_id: UUID,
) -> StartCallSchema:
    """
    Starts a new Twilio Video room with journey_id as a name
    and updates the twilio conversation's attributes.
    """
    journey_service = JourneyService(session)
    journey = journey_service.get_journey_by_id(journey_id)
    if not journey:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"Journey with with id={journey_id} not found",
        )

    if current_user.id not in [journey.match.user1_id, journey.match.user2_id]:
        raise HTTPException(
            status_code=http_status.HTTP_401_UNAUTHORIZED,
            detail="User not related to this journey",
        )

    twilio_service = TwilioService()
    try:
        # 1. Create a new Twilio Video or Audio Room + set the webhook
        video_room = twilio_service.video_service.rooms.create(
            unique_name=str(journey_id),
            max_participants=2,
            status_callback=settings.TWILIO_VIDEO_WEBHOOK_URL,
            status_callback_method="POST",
        )

        # 2. Send a chat message to all participants to notify them
        # The client-side app will:
        # - listen for this message
        # - ask user to join
        # - request token "call-token" and then join the room
        twilio_service.chat_service.conversations(str(journey.id)).messages.create(
            x_twilio_webhook_enabled="true",
            author="system",
            subject="new_call",
            body=f"{video_room.unique_name}",
        )

        return {
            "message": "Call successfully initiated.",
            "room_name": video_room.unique_name,
        }

    except Exception as e:
        print(f"Error starting video call: {e}")
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=str(e))
