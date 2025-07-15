from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.models.enums import MessageType


class MessageBase(BaseModel):
    """
    Base schema for message data
    """

    journey_id: UUID
    sender_id: UUID
    content: str
    message_type: str = Field(default=MessageType.TEXT.value)

    @field_validator("message_type")
    def validate_message_type(cls, v):
        if v not in [mtype.value for mtype in MessageType]:
            raise ValueError(
                f"Invalid message type. Must be one of: {[mtype.value for mtype in MessageType]}"
            )
        return v


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
    is_read: bool = False
    sent_at: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


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


class MessageResponse(BaseModel):
    """
    Schema for detailed message response with sender information
    """

    id: UUID
    journey_id: UUID
    sender_id: UUID
    content: str
    message_type: str
    is_read: bool
    sent_at: datetime
    created_at: datetime
    updated_at: datetime
    sender_name: Optional[str] = None  # Sender's name for display
    sender_avatar: Optional[str] = None  # Sender's avatar URL

    class Config:
        from_attributes = True
