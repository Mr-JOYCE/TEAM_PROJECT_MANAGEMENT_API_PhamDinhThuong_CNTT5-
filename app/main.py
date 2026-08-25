from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.orm import Session

from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.db.database import get_db

from app.exceptions.handlers import (
    http_exception_handler,
    validation_exception_handler
)
from app.exceptions.handlers import integrity_exception_handler
from app.routers.auth import router as auth_router
from app.routers.admin import router as admin_router
from app.routers.users import router as users_router
from app.routers.projects import router as projects_router
from app.routers.tasks import router as tasks_router

app = FastAPI(
    title="Project Management API",
    version="1.0.0",
    description="API quản lý người dùng, dự án, task, bình luận và file đính kèm.",
    openapi_tags=[
        {"name": "Authentication", "description": "Đăng ký, đăng nhập và làm mới JWT."},
        {"name": "Users", "description": "Thông tin cá nhân và danh sách người dùng (admin)."},
        {"name": "Admin", "description": "Các endpoint dành cho quản trị viên."},
        {"name": "Projects", "description": "CRUD dự án và quản lý thành viên."},
        {"name": "Tasks", "description": "CRUD task, bình luận và file đính kèm."},
        {"name": "System", "description": "Kiểm tra trạng thái dịch vụ."},
    ],
)

app.add_exception_handler(
    StarletteHTTPException,
    http_exception_handler
)

app.add_exception_handler(
    RequestValidationError,
    validation_exception_handler
)
app.add_exception_handler(
    IntegrityError,
    integrity_exception_handler
)

app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(users_router)
app.include_router(projects_router)
app.include_router(tasks_router)

@app.get("/", tags=["System"], summary="Giới thiệu API")
def root():
    return {
        "message": "Project Management API"
    }

@app.get(
    "/health",
    tags=["System"],
    summary="Kiểm tra sức khỏe API và database",
    responses={200: {"description": "API phản hồi; database có thể connected hoặc disconnected."}},
)
def health_check(
    db: Session = Depends(get_db)
):
    try:
        db.execute(text("SELECT 1"))

        return {
            "status": "ok",
            "database": "connected"
        }

    except Exception:
        return {
            "status": "error",
            "database": "disconnected"
        }