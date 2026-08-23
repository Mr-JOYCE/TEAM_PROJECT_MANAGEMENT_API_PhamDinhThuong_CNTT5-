import jwt
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import (
	create_access_token,
	create_refresh_token,
	hash_password,
	verify_password,
)
from app.core.config import settings
from app.exceptions.error import (
	BadRequestException,
	ForbiddenException,
	UnauthorizedException,
)
from app.models.user import User
from app.schemas.user import RefreshTokenRequest, TokenResponse, UserCreate, UserLogin


def register_user(db: Session, user_data: UserCreate) -> User:
	existing_user = db.scalar(
		select(User).where(User.email == user_data.email)
	)
	if existing_user is not None:
		raise BadRequestException("Email already registered")

	user = User(
		email=user_data.email,
		password_hash=hash_password(user_data.password),
		full_name=user_data.full_name,
		role=user_data.role,
	)
	db.add(user)
	try:
		db.commit()
	except IntegrityError:
		db.rollback()
		raise BadRequestException("Email already registered")
	db.refresh(user)
	return user


def login_user(db: Session, credentials: UserLogin) -> TokenResponse:
	user = db.scalar(
		select(User).where(User.email == credentials.email)
	)
	if user is None or not verify_password(
		credentials.password,
		user.password_hash,
	):
		raise UnauthorizedException()

	if not user.is_active:
		raise ForbiddenException("User account is inactive")

	return TokenResponse(
		access_token=create_access_token(str(user.id)),
		refresh_token=create_refresh_token(str(user.id)),
	)


def refresh_access_token(db: Session, token_data: RefreshTokenRequest) -> TokenResponse:
	try:
		payload = jwt.decode(
			token_data.refresh_token,
			settings.SECRET_KEY,
			algorithms=[settings.JWT_ALGORITHM],
		)
		if payload.get("type") != "refresh":
			raise UnauthorizedException("Invalid refresh token")
		user_id = int(payload.get("sub"))
	except jwt.ExpiredSignatureError:
		raise UnauthorizedException("Refresh token has expired")
	except (jwt.PyJWTError, TypeError, ValueError):
		raise UnauthorizedException("Invalid refresh token")

	user = db.scalar(select(User).where(User.id == user_id))
	if user is None:
		raise UnauthorizedException("User not found")
	if not user.is_active:
		raise ForbiddenException("User account is inactive")

	return TokenResponse(
		access_token=create_access_token(str(user.id)),
		refresh_token=create_refresh_token(str(user.id)),
	)
