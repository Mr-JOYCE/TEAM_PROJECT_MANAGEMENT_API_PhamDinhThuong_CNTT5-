from datetime import datetime

from sqlalchemy import and_, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.exceptions.error import BadRequestException, ForbiddenException, NotFoundException
from app.models.audit_log import AuditLog
from app.models.project import Project
from app.models.project_member import ProjectMember, ProjectMemberRole
from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectUpdate


def _get_project(db: Session, project_id: int) -> Project:
    project = db.scalar(
        select(Project).where(
            Project.id == project_id,
            Project.is_deleted.is_(False),
        )
    )
    if project is None:
        raise NotFoundException("Project not found")
    return project


def _require_member(db: Session, project_id: int, user_id: int) -> ProjectMember:
    membership = db.scalar(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id,
        )
    )
    if membership is None:
        raise ForbiddenException("You are not a project member")
    return membership


def _require_owner(db: Session, project_id: int, user_id: int) -> Project:
    project = _get_project(db, project_id)
    membership = _require_member(db, project_id, user_id)
    if membership.role != ProjectMemberRole.OWNER:
        raise ForbiddenException("Only the project owner can perform this action")
    return project


def _audit(db: Session, actor_id: int, project_id: int, action: str, details: str):
    db.add(AuditLog(
        actor_id=actor_id,
        project_id=project_id,
        action=action,
        details=details,
    ))


def create_project(db: Session, data: ProjectCreate, owner: User) -> Project:
    project = Project(name=data.name, description=data.description, owner_id=owner.id)
    try:
        db.add(project)
        db.flush()
        db.add(ProjectMember(
            project_id=project.id,
            user_id=owner.id,
            role=ProjectMemberRole.OWNER,
        ))
        _audit(db, owner.id, project.id, "PROJECT_CREATED", project.name)
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(project)
    return project


def list_projects(db: Session, user_id: int, search: str | None = None) -> list[Project]:
    query = (
        select(Project)
        .join(ProjectMember, ProjectMember.project_id == Project.id)
        .where(
            ProjectMember.user_id == user_id,
            Project.is_deleted.is_(False),
        )
        .order_by(Project.id)
    )
    if search:
        query = query.where(Project.name.ilike(f"%{search.strip()}%"))
    return list(db.scalars(query).unique().all())


def get_project(db: Session, project_id: int, user_id: int) -> Project:
    project = _get_project(db, project_id)
    _require_member(db, project.id, user_id)
    return project


def update_project(db: Session, project_id: int, data: ProjectUpdate, owner: User) -> Project:
    project = _require_owner(db, project_id, owner.id)
    changes = data.model_dump(exclude_unset=True)
    if not changes:
        raise BadRequestException("No project fields to update")
    for field, value in changes.items():
        setattr(project, field, value)
    _audit(db, owner.id, project.id, "PROJECT_UPDATED", ",".join(changes))
    db.commit()
    db.refresh(project)
    return project


def delete_project(db: Session, project_id: int, owner: User) -> None:
    project = _require_owner(db, project_id, owner.id)
    project.is_deleted = True
    project.deleted_at = datetime.now()
    _audit(db, owner.id, project.id, "PROJECT_DELETED", project.name)
    db.commit()


def add_member(db: Session, project_id: int, user_id: int, owner: User) -> ProjectMember:
    project = _require_owner(db, project_id, owner.id)
    user = db.get(User, user_id)
    if user is None:
        raise NotFoundException("User not found")
    if db.scalar(select(ProjectMember).where(
        ProjectMember.project_id == project_id,
        ProjectMember.user_id == user_id,
    )) is not None:
        raise BadRequestException("User is already a project member")
    member = ProjectMember(
        project_id=project_id,
        user_id=user_id,
        role=ProjectMemberRole.MEMBER,
    )
    db.add(member)
    _audit(db, owner.id, project_id, "MEMBER_ADDED", str(user_id))
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise BadRequestException("User is already a project member")
    db.refresh(member)
    return member


def remove_member(db: Session, project_id: int, user_id: int, owner: User) -> None:
    _require_owner(db, project_id, owner.id)
    member = _require_member(db, project_id, user_id)
    if member.role == ProjectMemberRole.OWNER:
        raise BadRequestException("The project owner cannot be removed")
    db.delete(member)
    _audit(db, owner.id, project_id, "MEMBER_REMOVED", str(user_id))
    db.commit()


def list_members(db: Session, project_id: int, user_id: int) -> list[ProjectMember]:
    _require_member(db, project_id, user_id)
    return list(db.scalars(
        select(ProjectMember)
        .where(ProjectMember.project_id == project_id)
        .order_by(ProjectMember.joined_at)
    ).all())