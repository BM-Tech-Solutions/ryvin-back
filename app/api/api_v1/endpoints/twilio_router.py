from pprint import pprint as print
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Response, UploadFile
from fastapi import status as http_status
from firebase_admin import messaging
from pydantic import BaseModel
from twilio.request_validator import RequestValidator
from twilio.twiml.voice_response import VoiceResponse

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.dependencies import FlexUserDep, SessionDep
from app.models.enums import TwilioEvent
from app.services.journey_service import JourneyService, MessageService
from app.services.match_service import MatchService
from app.services.twilio_service import TwilioService

router = APIRouter()


# Schemas
class TwilioChatTokenOut(BaseModel):
    user_id: str
    chat_token: str


class TwilioVideoTokenOut(BaseModel):
    user_id: str
    video_token: str


class TwilioVoiceTokenOut(BaseModel):
    user_id: str
    voice_token: str


class StartVideoOut(BaseModel):
    room_name: str
    video_token: str


# verify twilio signature
class TwilioSignatureValidator:
    def __init__(self, url: str):
        self.url = url

    async def __call__(self, request: Request):
        url = self.url
        twilio_sig = request.headers.get("X-Twilio-Signature") or ""

        body = await request.form()
        body = dict(body)

        validator = RequestValidator(settings.TWILIO_AUTH_TOKEN)
        if not validator.validate(url, body, twilio_sig):
            print("Invalid Twilio signature:")
            print(f"{url= }")
            print(f"{body= }")
            print(f"{twilio_sig= }")
            raise HTTPException(
                status_code=http_status.HTTP_403_FORBIDDEN,
                detail="Invalid Twilio signature.",
            )
        return body


ChatWebhookBodyDep = Annotated[
    dict[str, UploadFile | str],
    Depends(TwilioSignatureValidator(url=settings.TWILIO_CHAT_WEBHOOK_URL)),
]
VideoWebhookBodyDep = Annotated[
    dict[str, UploadFile | str],
    Depends(TwilioSignatureValidator(url=settings.TWILIO_VIDEO_WEBHOOK_URL)),
]
VoiceWebhookBodyDep = Annotated[
    dict[str, UploadFile | str],
    Depends(TwilioSignatureValidator(url=settings.TWILIO_VOICE_WEBHOOK_URL)),
]
VoiceRequestBodyDep = Annotated[
    dict[str, UploadFile | str],
    Depends(TwilioSignatureValidator(url=settings.TWILIO_VOICE_REQUEST_URL)),
]


# chat
@router.get("/chat-token", openapi_extra={"security": []})
async def get_twilio_chat_token(current_user: FlexUserDep) -> TwilioChatTokenOut:
    # Create the access token
    twilio_service = TwilioService()
    token = twilio_service.get_chat_token(user_id=str(current_user.id))

    return {"user_id": str(current_user.id), "chat_token": token}


@router.post("/chat-webhook", openapi_extra={"security": []})
def twilio_chat_webhook(session: SessionDep, body: ChatWebhookBodyDep):
    print("Twilio Chat Webhook:")
    print(body)

    try:
        msg_service = MessageService(session)
        if body.get("EventType") == TwilioEvent.ON_MESSAGE_ADDED:
            msg = msg_service.create_message(body)
            if msg:
                try:
                    msg.send_notif_to_reciever(title="new msg added")
                except Exception as e:
                    print(f"error sending new msg notif: {type(e)}")
                    print(f"{e}")

        if body.get("EventType") == TwilioEvent.ON_MESSAGE_UPDATED:
            msg_service.update_message(body)
        if body.get("EventType") == TwilioEvent.ON_MESSAGE_REMOVED:
            msg_service.delete_message(body)

    except Exception as e:
        print(f"Error Handling Webhook '{body.get('EventType')}':")
        print(f"\t{e}")

    return {}


# video
@router.get("/video-token/{journey_id}", openapi_extra={"security": []})
async def get_twilio_video_token(
    session: SessionDep, current_user: FlexUserDep, journey_id: UUID
) -> TwilioVideoTokenOut:
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

    twilio_service = TwilioService()
    token = twilio_service.get_video_token(user_id=str(current_user.id), room_name=room_name)

    return {"user_id": str(current_user.id), "video_token": token}


@router.post("/video-webhook", openapi_extra={"security": []})
async def twilio_video_webhook(body: VideoWebhookBodyDep):
    print("Twilio Video Webhook:")
    print(body)
    return {}


@router.get("/start-video/{journey_id}", openapi_extra={"security": []})
def start_video(session: SessionDep, current_user: FlexUserDep, journey_id: UUID) -> StartVideoOut:
    """
    Starts a new Twilio Video room with journey_id as a name
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

    room_name = str(journey_id)
    twilio_service = TwilioService()

    try:
        video_room = twilio_service.get_room(room_name)
        if not video_room:
            video_room = twilio_service.create_room(room_name=room_name)
        other_user = journey.match.get_other_user(current_user.id)
        other_user_token = twilio_service.get_video_token(str(other_user.id), room_name)
        current_user_token = twilio_service.get_video_token(str(current_user.id), room_name)

        if other_user.firebase_token:
            msg = messaging.Message(
                token=other_user.firebase_token,
                notification=messaging.Notification(title="New Call"),
                data={"room_name": room_name, "video_token": other_user_token},
            )
        messaging.send(msg)

        return {"room_name": room_name, "video_token": current_user_token}

    except Exception as e:
        print(f"Error starting video call: {e}")
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=str(e))


# voice
@router.get("/voice-token", openapi_extra={"security": []})
async def get_twilio_voice_token(current_user: FlexUserDep) -> TwilioVoiceTokenOut:
    twilio_service = TwilioService()
    token = twilio_service.get_voice_token(user_id=str(current_user.id))

    return {"user_id": str(current_user.id), "voice_token": token}


@router.post("/voice-webhook", openapi_extra={"security": []})
async def twilio_voice_webhook(body: VoiceWebhookBodyDep):
    print("Twilio Voice Webhook:")
    print(body)
    return {}


@router.post("/voice-request", openapi_extra={"security": []})
async def twilio_voice_request(body: VoiceRequestBodyDep):
    caller = body.get("From")
    recipient = body.get("To")

    print(f"Incoming call from '{caller}' to '{recipient}'")
    print(body)

    if caller and caller.startswith("client:"):
        caller = caller.removeprefix("client:")

    if recipient and recipient.startswith("client:"):
        recipient = recipient.removeprefix("client:")

    response = VoiceResponse()
    with SessionLocal() as sess:
        service = MatchService(sess)
        try:
            match = service.get_match_by_users(caller, recipient)
            # TODO: add validation for Journey Step
        except Exception:
            match = None

    if match:
        response.dial(callerId=caller).client(recipient)
    else:
        response.reject(reason="fastapi rejected this.")

    return Response(content=str(response), media_type="text/xml")
