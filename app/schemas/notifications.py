from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class NotificationUpdate(BaseModel):
    """
    Base schema for notification data
    """

    is_ready: bool


class NotificationOut(BaseModel):
    """
    Base schema for notification response
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    title: str
    body: str
    is_ready: bool
    created_at: datetime
    updated_at: datetime
