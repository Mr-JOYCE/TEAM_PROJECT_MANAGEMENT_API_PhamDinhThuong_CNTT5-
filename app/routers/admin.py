from fastapi import APIRouter, Depends

from app.dependencies.auth import get_current_admin_user
from app.models.user import User
from app.schemas.user import UserResponse


router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/me", response_model=UserResponse, summary="Xem hồ sơ quản trị viên", responses={401: {"description": "Chưa xác thực."}, 403: {"description": "Chỉ ADMIN được phép."}})
def get_admin_profile(
    current_admin: User = Depends(get_current_admin_user),
):
	return current_admin
