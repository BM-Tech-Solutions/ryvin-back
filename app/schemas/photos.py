from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class PhotoBase(BaseModel):
    """
    Base schema for photos
    """

    model_config = ConfigDict(from_attributes=True)

    file_path: str
    is_primary: bool


class PhotoOut(PhotoBase):
    """
    Schema for Photo Response
    """

    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime
