from datetime import datetime
from pydantic import BaseModel, ConfigDict

from app.models.task import TaskPriority, TaskStatus

class TaskBase(BaseModel):
    title: str
    description: str | None = None
    assignee_id: int | None = None
    status: TaskStatus = TaskStatus.TODO
    priority: TaskPriority = TaskPriority.MEDIUM
    due_date: datetime | None = None

class TaskCreate(TaskBase):
    pass

class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    assignee_id: int | None = None
    status: TaskStatus | None = None
    priority: TaskPriority | None = None
    due_date: datetime | None = None

class TaskResponse(TaskBase):
    id: int
    project_id: int
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )