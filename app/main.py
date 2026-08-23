from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.orm import Session

from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.db.database import get_db

from app.exceptions.handlers import (
    http_exception_handler,
    validation_exception_handler
)
from app.routers.auth import router as auth_router
from app.routers.admin import router as admin_router
from app.routers.users import router as users_router

app = FastAPI(
    title="Project Management API",
    version="1.0.0"
)

app.add_exception_handler(
    StarletteHTTPException,
    http_exception_handler
)

app.add_exception_handler(
    RequestValidationError,
    validation_exception_handler
)

app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(users_router)

@app.get("/")
def root():
    return {
        "message": "Project Management API"
    }

@app.get("/health")
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