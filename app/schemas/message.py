from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, ValidationInfo, field_validator

from app.core.database import Session
from app.models.enums import MessageType
from app.services import PhotoService, QuestionnaireService


class MessageBase(BaseModel):
    """
    Base schema for message data
    """

    model_config = ConfigDict(from_attributes=True)

    content: str
    message_type: MessageType = MessageType.TEXT


class MessageCreate(MessageBase):
    """
    Schema for message creation
    """

    pass


class MessageInDBBase(MessageBase):
    """
    Base schema for message in DB
    """

    id: UUID
    sender_id: UUID
    journey_id: UUID
    is_read: bool = False
    sent_at: datetime
    created_at: datetime
    updated_at: datetime


class MessageInDB(MessageInDBBase):
    """
    Schema for message in DB (internal use)
    """

    pass


class Message(MessageInDBBase):
    """
    Schema for message response
    """

    pass


class Sender(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    first_name: Optional[str] = None
    avatar: Optional[str] = None


class MessageOut(BaseModel):
    """
    Schema for detailed message response with sender information
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    journey_id: UUID
    sender_id: UUID
    content: str
    message_type: str
    is_read: bool
    sent_at: datetime
    created_at: datetime
    updated_at: datetime
    sender: Sender

    @field_validator("sender", mode="before")
    @classmethod
    def validate_sender(cls, value, info: ValidationInfo):
        sender_id = info.data.get("sender_id")
        with Session() as sess:
            quest_service = QuestionnaireService(sess)
            photo_service = PhotoService(sess)
            quest = quest_service.get_questionnaire(sender_id)
            primary_photo = photo_service.get_user_primary_photo(sender_id)
            return {
                "first_name": quest.first_name if quest else None,
                "avatar": primary_photo.file_path if primary_photo else None,
            }
