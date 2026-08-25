from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.exceptions.error import UnauthorizedException
from app.schemas.user import (
	RefreshTokenRequest,
	TokenResponse,
	UserCreate,
	UserLogin,
	UserResponse,
)
from app.services.auth_service import login_user, refresh_access_token, register_user
from app.services.rate_limit import (
	ensure_login_allowed,
	record_login_failure,
	reset_login_attempts,
)


router = APIRouter(prefix="/auth", tags=["Authentication"])


class LoginForm:
	def __init__(
		self,
		email: str | None = Form(None, description="Account email"),
		username: str | None = Form(
			None,
			description="Account email (OAuth2 compatibility)",
		),
		password: str = Form(...),
	):
		self.email = email or username
		self.password = password


@router.post(
	"/register",
	response_model=UserResponse,
	status_code=status.HTTP_201_CREATED,
summary="Đăng ký tài khoản",
description="Tạo tài khoản USER mới. Email phải là duy nhất.",
responses={400: {"description": "Email đã được đăng ký."}, 422: {"description": "Dữ liệu đầu vào không hợp lệ."}},
)
def register(
	user_data: UserCreate,
	db: Session = Depends(get_db),
):
	return register_user(db, user_data)


@router.post(
	"/login",
	response_model=TokenResponse,
	summary="Đăng nhập",
	description="Xác thực bằng email và password để nhận access token và refresh token.",
	responses={401: {"description": "Sai thông tin đăng nhập."}, 403: {"description": "Tài khoản bị vô hiệu hóa."}, 429: {"description": "Quá nhiều lần đăng nhập thất bại."}},
)
def login(
	request: Request,
	form_data: LoginForm = Depends(),
	db: Session = Depends(get_db),
):
	try:
		credentials = UserLogin(
			email=form_data.email,
			password=form_data.password,
		)
	except ValidationError as exc:
		raise RequestValidationError(exc.errors()) from exc
	key = f"{credentials.email}:{request.client.host if request.client else 'unknown'}"
	ensure_login_allowed(key)
	try:
		result = login_user(db, credentials)
	except UnauthorizedException:
		record_login_failure(key)
		raise
	reset_login_attempts(key)
	return result


@router.post(
	"/refresh",
	response_model=TokenResponse,
	summary="Làm mới token",
	description="Đổi refresh token hợp lệ lấy một cặp access/refresh token mới.",
	responses={401: {"description": "Refresh token không hợp lệ hoặc đã hết hạn."}, 403: {"description": "Tài khoản bị vô hiệu hóa."}},
)
def refresh(
	token_data: RefreshTokenRequest,
	db: Session = Depends(get_db),
):
	return refresh_access_token(db, token_data)
