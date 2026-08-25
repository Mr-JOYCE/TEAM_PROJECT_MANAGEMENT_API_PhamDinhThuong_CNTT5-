from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TaskAttachmentResponse(BaseModel):
    id: int
    task_id: int
    filename: str
    content_type: str
    size: int
    path: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
