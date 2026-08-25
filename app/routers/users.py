from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_admin_user, get_current_user
from app.db.database import get_db
from app.models.user import User
from app.schemas.user import UserResponse
from app.services.user_service import get_users


router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserResponse, summary="Xem hồ sơ của tôi", responses={401: {"description": "Chưa xác thực."}})
def get_me(current_user: User = Depends(get_current_user)):
	return current_user


@router.get("", response_model=list[UserResponse], summary="Liệt kê người dùng", description="Chỉ ADMIN được xem danh sách người dùng.", responses={401: {"description": "Chưa xác thực."}, 403: {"description": "Chỉ ADMIN được phép."}})
def list_users(
	search: str | None = Query(default=None),
	is_active: bool | None = Query(default=None),
	_: User = Depends(get_current_admin_user),
	db: Session = Depends(get_db),
):
	return get_users(db, search=search, is_active=is_active)
