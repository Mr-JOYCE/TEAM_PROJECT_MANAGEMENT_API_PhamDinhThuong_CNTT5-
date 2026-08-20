from datetime import datetime
from pydantic import BaseModel, ConfigDict

from app.models.project_member import ProjectMemberRole

class ProjectMemberBase(BaseModel):
    user_id: int
    role: ProjectMemberRole = ProjectMemberRole.MEMBER

class ProjectMemberCreate(ProjectMemberBase):
    pass

class ProjectMemberUpdate(BaseModel):
    role: ProjectMemberRole

class ProjectMemberResponse(ProjectMemberBase):
    project_id: int
    joined_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )