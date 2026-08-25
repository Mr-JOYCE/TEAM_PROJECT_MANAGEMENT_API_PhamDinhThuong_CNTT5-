from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class TaskCommentCreate(BaseModel):
    content: str = Field(min_length=1, max_length=10000)


class TaskCommentResponse(TaskCommentCreate):
    id: int
    task_id: int
    author_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
