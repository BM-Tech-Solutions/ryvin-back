from contextlib import suppress

from twilio.base.exceptions import TwilioRestException
from twilio.jwt.access_token import AccessToken
from twilio.jwt.access_token.grants import ChatGrant, VideoGrant
from twilio.rest import Client

from app.core.config import settings
from app.models import Journey
from app.models.enums import TwilioEvent


class TwilioService:
    def __init__(self):
        self.client = Client(
            account_sid=settings.TWILIO_ACCOUNT_SID,
            username=settings.TWILIO_API_KEY_SID,
            password=settings.TWILIO_API_KEY_SECRET,
        )

        self.chat_service = self.client.conversations.v1.services(settings.TWILIO_SERVICE_SID)
        self.video_service = self.client.video.v1

    def get_chat_token(self, user_id: str):
        # Create the access token for the Chat/Conversations Service
        token = AccessToken(
            account_sid=settings.TWILIO_ACCOUNT_SID,
            signing_key_sid=settings.TWILIO_API_KEY_SID,
            secret=settings.TWILIO_API_KEY_SECRET,
            grants=[ChatGrant(service_sid=settings.TWILIO_SERVICE_SID)],
            ttl=settings.TWILIO_ACCESS_TOKEN_TTL_SECONDS,
            identity=user_id,
        )

        return token.to_jwt()

    def get_call_token(self, user_id: str, room_name: str):
        # Create the access token for the Video Service
        token = AccessToken(
            account_sid=settings.TWILIO_ACCOUNT_SID,
            signing_key_sid=settings.TWILIO_API_KEY_SID,
            secret=settings.TWILIO_API_KEY_SECRET,
            grants=[VideoGrant(room=room_name)],
            ttl=settings.TWILIO_ACCESS_TOKEN_TTL_SECONDS,
            identity=user_id,
        )

        return token.to_jwt()

    def get_user(self, user_id: str):
        with suppress(TwilioRestException):
            return self.chat_service.users(user_id).fetch()
        return None

    def create_user(self, user_id: str):
        with suppress(TwilioRestException):
            return self.chat_service.users.create(
                identity=user_id, role_sid=settings.TWILIO_SERVICE_ROLE_SID
            )
        return None

    def create_conversation(self, journey: Journey):
        # make sure users are created (it's ok if they already exist)
        self.create_user(journey.match.user1_id)
        self.create_user(journey.match.user2_id)
        conv = self.get_conversation(journey.id)
        if not conv:
            conv = self.chat_service.conversations.create(unique_name=journey.id)

        with suppress(TwilioRestException):
            conv.participants.create(
                identity=journey.match.user1_id,
                role_sid=settings.TWILIO_CHANNEL_ROLE_SID,
            )
        with suppress(TwilioRestException):
            conv.participants.create(
                identity=journey.match.user2_id,
                role_sid=settings.TWILIO_CHANNEL_ROLE_SID,
            )
        return conv

    def get_conversation(self, conv_sid: str):
        with suppress(TwilioRestException):
            return self.chat_service.conversations(conv_sid).fetch()
        return None

    def register_webhook(self, events: list[TwilioEvent] = None):
        if events is None:
            events = [event.value for event in TwilioEvent]

        try:
            if not settings.TWILIO_CHAT_WEBHOOK_URL.strip():
                raise Exception("webhook url not provided")
            webhook = self.chat_service.configuration.webhooks().update(
                pre_webhook_url=settings.TWILIO_CHAT_WEBHOOK_URL,
                post_webhook_url=settings.TWILIO_CHAT_WEBHOOK_URL,
                filters=events,
                method="POST",
            )
            print("Twilio Webhook Registration Success:")
            print(f"webhook url: '{settings.TWILIO_CHAT_WEBHOOK_URL}'")
            return webhook
        except TwilioRestException as e:
            print("Twilio Webhook Registration Failed:")
            print(f"Error: {e}")
            print(f"webhook url: '{settings.TWILIO_CHAT_WEBHOOK_URL}'")
            print(f"events: {events}")
            print(e.status)
            print(e.msg)
        except Exception as e:
            print("Twilio Webhook Registration Failed:")
            print(f"Error: {e}")
            print(f"webhook url: '{settings.TWILIO_CHAT_WEBHOOK_URL}'")
            print(f"events: {events}")
