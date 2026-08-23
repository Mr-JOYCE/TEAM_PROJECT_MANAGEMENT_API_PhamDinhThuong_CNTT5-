from datetime import datetime
import enum

from sqlalchemy import DateTime, Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db.database import Base

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.user import User

class ProjectMemberRole(str, enum.Enum):
    OWNER = "OWNER"
    MEMBER = "MEMBER"

class ProjectMember(Base):
    __tablename__ = "project_members"

    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id"),
        primary_key=True
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        primary_key=True
    )

    role: Mapped[ProjectMemberRole] = mapped_column(
        Enum(ProjectMemberRole),
        nullable=False
    )

    joined_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
        nullable=False
    )

    project: Mapped["Project"] = relationship(
        "Project",
        back_populates="members"
    )

    user: Mapped["User"] = relationship(
        "User",
        back_populates="project_memberships"
    )