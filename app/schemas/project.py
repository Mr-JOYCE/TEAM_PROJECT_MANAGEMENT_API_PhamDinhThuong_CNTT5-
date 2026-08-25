from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator

class ProjectBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        value = " ".join(value.split())
        if not value:
            raise ValueError("Project name must not be empty")
        return value

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str | None) -> str | None:
        if value is None:
            return value
        value = " ".join(value.split())
        if not value:
            raise ValueError("Project name must not be empty")
        return value

class ProjectResponse(ProjectBase):
    id: int
    owner_id: int
    created_at: datetime
    deleted_at: datetime | None = None
    is_deleted: bool = False

    model_config = ConfigDict(
        from_attributes=True
    )