from pathlib import Path
from typing import BinaryIO

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.exceptions.error import BadRequestException, ForbiddenException, NotFoundException
from app.models.project_member import ProjectMember, ProjectMemberRole
from app.models.project import Project
from app.models.task import Task
from app.models.task_attachment import TaskAttachment
from app.models.task_comment import TaskComment
from app.models.user import User
from app.schemas.task import TaskCreate, TaskUpdate
from app.schemas.task_comment import TaskCommentCreate


def _membership(db: Session, project_id: int, user_id: int) -> ProjectMember:
    project = db.scalar(
        select(Project).where(
            Project.id == project_id,
            Project.is_deleted.is_(False),
        )
    )
    if project is None:
        raise NotFoundException("Project not found")
    membership = db.scalar(select(ProjectMember).where(
        ProjectMember.project_id == project_id,
        ProjectMember.user_id == user_id,
    ))
    if membership is None:
        raise ForbiddenException("You are not a project member")
    return membership


def _task(db: Session, task_id: int) -> Task:
    task = db.get(Task, task_id)
    if task is None:
        raise NotFoundException("Task not found")
    return task


def _authorized_task(db: Session, task_id: int, user_id: int) -> tuple[Task, ProjectMember]:
    task = _task(db, task_id)
    return task, _membership(db, task.project_id, user_id)


def _validate_assignee(db: Session, project_id: int, assignee_id: int | None) -> None:
    if assignee_id is not None:
        _membership(db, project_id, assignee_id)


def create_task(db: Session, project_id: int, data: TaskCreate, user: User) -> Task:
    _membership(db, project_id, user.id)
    _validate_assignee(db, project_id, data.assignee_id)
    task = Task(project_id=project_id, **data.model_dump())
    db.add(task)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise BadRequestException("Task data conflicts with existing data")
    db.refresh(task)
    return task


def list_tasks(
    db: Session,
    project_id: int,
    user_id: int,
    status=None,
    priority=None,
    assignee_id: int | None = None,
    search: str | None = None,
    limit: int = 20,
    offset: int = 0,
    sort: str = "created_at",
    order: str = "desc",
) -> list[Task]:
    _membership(db, project_id, user_id)
    query = select(Task).where(Task.project_id == project_id)
    if status is not None:
        query = query.where(Task.status == status)
    if priority is not None:
        query = query.where(Task.priority == priority)
    if assignee_id is not None:
        _validate_assignee(db, project_id, assignee_id)
        query = query.where(Task.assignee_id == assignee_id)
    if search:
        query = query.where(Task.title.ilike(f"%{search.strip()}%"))
    sort_column = Task.due_date if sort == "due_date" else Task.created_at
    query = query.order_by(sort_column.asc() if order == "asc" else sort_column.desc())
    return list(db.scalars(query.offset(offset).limit(limit)).all())


def get_task(db: Session, task_id: int, user_id: int) -> Task:
    task, _ = _authorized_task(db, task_id, user_id)
    return task


def update_task(db: Session, task_id: int, data: TaskUpdate, user: User) -> Task:
    task, membership = _authorized_task(db, task_id, user.id)
    changes = data.model_dump(exclude_unset=True)
    if not changes:
        raise BadRequestException("No task fields to update")
    if membership.role != ProjectMemberRole.OWNER:
        if "assignee_id" in changes:
            raise ForbiddenException("Only the project owner can change the assignee")
        allowed_fields = {"status", "description"} if task.assignee_id == user.id else {
            "title", "description", "due_date", "priority",
        }
        if set(changes) - allowed_fields:
            raise ForbiddenException("You do not have permission to update these task fields")
    _validate_assignee(db, task.project_id, changes.get("assignee_id", task.assignee_id))
    for field, value in changes.items():
        setattr(task, field, value)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise BadRequestException("Task data conflicts with existing data")
    db.refresh(task)
    return task


def delete_task(db: Session, task_id: int, user: User) -> None:
    task, membership = _authorized_task(db, task_id, user.id)
    if membership.role != ProjectMemberRole.OWNER:
        raise ForbiddenException("Only the project owner can delete tasks")
    db.delete(task)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise BadRequestException("Comment could not be created")


def list_comments(db: Session, task_id: int, user_id: int) -> list[TaskComment]:
    task, _ = _authorized_task(db, task_id, user_id)
    return list(db.scalars(select(TaskComment).where(TaskComment.task_id == task.id).order_by(TaskComment.created_at)).all())


def create_comment(db: Session, task_id: int, data: TaskCommentCreate, user: User) -> TaskComment:
    task, _ = _authorized_task(db, task_id, user.id)
    comment = TaskComment(task_id=task.id, author_id=user.id, content=data.content)
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment


ALLOWED_ATTACHMENT_TYPES = {
    "application/pdf", "image/jpeg", "image/png", "text/plain",
    "application/zip", "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}
ALLOWED_ATTACHMENT_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png", ".txt", ".zip", ".docx"}
MAX_ATTACHMENT_SIZE = 10 * 1024 * 1024


def save_attachment(
    db: Session,
    task_id: int,
    user: User,
    filename: str,
    content_type: str,
    file: BinaryIO,
    upload_root: Path = Path("uploads") / "tasks",
) -> TaskAttachment:
    task, _ = _authorized_task(db, task_id, user.id)
    safe_name = Path(filename or "attachment").name
    if content_type not in ALLOWED_ATTACHMENT_TYPES:
        raise BadRequestException("Unsupported attachment type")
    extension = Path(safe_name).suffix.lower()
    if extension not in ALLOWED_ATTACHMENT_EXTENSIONS or len(safe_name) > 255:
        raise BadRequestException("Invalid attachment filename")
    try:
        data = file.read(MAX_ATTACHMENT_SIZE + 1)
    except OSError as exc:
        raise BadRequestException("Attachment could not be read") from exc
    if len(data) > MAX_ATTACHMENT_SIZE:
        raise BadRequestException("Attachment exceeds the 10 MB limit")
    directory = upload_root / str(task.id)
    try:
        directory.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise BadRequestException("Attachment directory could not be created") from exc
    path = directory / safe_name
    try:
        path.write_bytes(data)
    except OSError as exc:
        raise BadRequestException("Attachment could not be saved") from exc
    attachment = TaskAttachment(
        task_id=task.id,
        filename=safe_name,
        content_type=content_type,
        size=len(data),
        path=str(path),
    )
    db.add(attachment)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise BadRequestException("Attachment could not be created")
    db.refresh(attachment)
    return attachment


def list_attachments(db: Session, task_id: int, user_id: int) -> list[TaskAttachment]:
    task, _ = _authorized_task(db, task_id, user_id)
    return list(db.scalars(select(TaskAttachment).where(TaskAttachment.task_id == task.id).order_by(TaskAttachment.created_at)).all())