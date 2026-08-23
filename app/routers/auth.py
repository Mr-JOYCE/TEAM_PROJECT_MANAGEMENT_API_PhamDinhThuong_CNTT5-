from fastapi import APIRouter, Depends, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.security import OAuth2PasswordRequestForm
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


@router.post(
	"/register",
	response_model=UserResponse,
	status_code=status.HTTP_201_CREATED,
)
def register(
	user_data: UserCreate,
	db: Session = Depends(get_db),
):
	return register_user(db, user_data)


@router.post("/login", response_model=TokenResponse)
def login(
	request: Request,
	form_data: OAuth2PasswordRequestForm = Depends(),
	db: Session = Depends(get_db),
):
	try:
		credentials = UserLogin(
			email=form_data.username,
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


@router.post("/refresh", response_model=TokenResponse)
def refresh(
	token_data: RefreshTokenRequest,
	db: Session = Depends(get_db),
):
	return refresh_access_token(db, token_data)
