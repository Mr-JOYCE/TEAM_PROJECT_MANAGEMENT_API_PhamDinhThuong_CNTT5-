from fastapi import APIRouter, Depends, File, Query, Response, UploadFile, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.dependencies.auth import get_current_user
from app.models.task import TaskPriority, TaskStatus
from app.models.user import User
from app.schemas.task import TaskCreate, TaskResponse, TaskUpdate
from app.schemas.task_attachment import TaskAttachmentResponse
from app.schemas.task_comment import TaskCommentCreate, TaskCommentResponse
from app.services.task_service import (
	create_comment,
	create_task,
	delete_task,
	get_task,
	list_attachments,
	list_comments,
	list_tasks,
	save_attachment,
	update_task,
)


router = APIRouter(tags=["Tasks"])


@router.post("/projects/{project_id}/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED, summary="Tạo task", description="Tạo task trong project; assignee nếu có phải là thành viên project.", responses={400: {"description": "Dữ liệu task xung đột."}, 403: {"description": "Không phải thành viên hoặc assignee không hợp lệ."}, 404: {"description": "Không tìm thấy project."}})
def create(
	project_id: int,
	data: TaskCreate,
	current_user: User = Depends(get_current_user),
	db: Session = Depends(get_db),
):
	return create_task(db, project_id, data, current_user)


@router.get("/projects/{project_id}/tasks", response_model=list[TaskResponse], summary="Liệt kê task", description="Lọc, tìm kiếm, phân trang và sắp xếp task trong project.", responses={403: {"description": "Không phải thành viên project."}, 404: {"description": "Không tìm thấy project."}})
def list_all(
	project_id: int,
	task_status: TaskStatus | None = Query(default=None, alias="status"),
	priority: TaskPriority | None = Query(default=None),
	assignee_id: int | None = Query(default=None, ge=1),
	search: str | None = Query(default=None),
	limit: int = Query(default=20, ge=1, le=100),
	offset: int = Query(default=0, ge=0),
	sort: str = Query(default="created_at", pattern="^(created_at|due_date)$"),
	order: str = Query(default="desc", pattern="^(asc|desc)$"),
	current_user: User = Depends(get_current_user),
	db: Session = Depends(get_db),
):
	return list_tasks(db, project_id, current_user.id, task_status, priority, assignee_id, search, limit, offset, sort, order)


@router.get("/tasks/{task_id}", response_model=TaskResponse, summary="Xem task", responses={403: {"description": "Không có quyền truy cập task."}, 404: {"description": "Không tìm thấy task."}})
def get_one(
	task_id: int,
	current_user: User = Depends(get_current_user),
	db: Session = Depends(get_db),
):
	return get_task(db, task_id, current_user.id)


@router.patch("/tasks/{task_id}", response_model=TaskResponse, summary="Cập nhật task", description="OWNER có toàn quyền; MEMBER chỉ cập nhật các field được phân quyền.", responses={400: {"description": "Không có field hoặc dữ liệu xung đột."}, 403: {"description": "Không đủ quyền cập nhật."}, 404: {"description": "Không tìm thấy task."}})
def update(
	task_id: int,
	data: TaskUpdate,
	current_user: User = Depends(get_current_user),
	db: Session = Depends(get_db),
):
	return update_task(db, task_id, data, current_user)


@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Xóa task", description="Chỉ OWNER của project được xóa task.", responses={204: {"description": "Xóa thành công."}, 403: {"description": "Chỉ OWNER được phép."}, 404: {"description": "Không tìm thấy task."}})
def delete(
	task_id: int,
	current_user: User = Depends(get_current_user),
	db: Session = Depends(get_db),
):
	delete_task(db, task_id, current_user)
	return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/tasks/{task_id}/comments", response_model=list[TaskCommentResponse], summary="Liệt kê bình luận", responses={403: {"description": "Không có quyền truy cập task."}, 404: {"description": "Không tìm thấy task."}})
def get_task_comments(
	task_id: int,
	current_user: User = Depends(get_current_user),
	db: Session = Depends(get_db),
):
	return list_comments(db, task_id, current_user.id)


@router.post("/tasks/{task_id}/comments", response_model=TaskCommentResponse, status_code=status.HTTP_201_CREATED, summary="Thêm bình luận", responses={400: {"description": "Bình luận xung đột dữ liệu."}, 403: {"description": "Không có quyền truy cập task."}, 404: {"description": "Không tìm thấy task."}})
def add_task_comment(
	task_id: int,
	data: TaskCommentCreate,
	current_user: User = Depends(get_current_user),
	db: Session = Depends(get_db),
):
	return create_comment(db, task_id, data, current_user)


@router.get("/tasks/{task_id}/attachments", response_model=list[TaskAttachmentResponse], summary="Liệt kê file đính kèm", responses={403: {"description": "Không có quyền truy cập task."}, 404: {"description": "Không tìm thấy task."}})
def get_task_attachments(
	task_id: int,
	current_user: User = Depends(get_current_user),
	db: Session = Depends(get_db),
):
	return list_attachments(db, task_id, current_user.id)


@router.post("/tasks/{task_id}/attachments", response_model=TaskAttachmentResponse, status_code=status.HTTP_201_CREATED, summary="Tải file đính kèm", description="Chấp nhận PDF, JPG, PNG, TXT, ZIP, DOCX; kích thước tối đa 10 MB.", responses={400: {"description": "Loại file, tên file, kích thước hoặc lưu file không hợp lệ."}, 403: {"description": "Không có quyền truy cập task."}, 404: {"description": "Không tìm thấy task."}})
def add_task_attachment(
	task_id: int,
	file: UploadFile = File(...),
	current_user: User = Depends(get_current_user),
	db: Session = Depends(get_db),
):
	return save_attachment(db, task_id, current_user, file.filename or "attachment", file.content_type or "", file.file)
