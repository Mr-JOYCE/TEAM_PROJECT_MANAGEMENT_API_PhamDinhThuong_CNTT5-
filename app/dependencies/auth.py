import jwt
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.database import get_db
from app.exceptions.error import ForbiddenException, UnauthorizedException
from app.models.user import User, UserRole


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/login",
    scheme_name="EmailBearer",
    description="Bearer JWT. Use the account email in the login form username field.",
)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        if payload.get("type") != "access":
            raise UnauthorizedException("Invalid access token")

        subject = payload.get("sub")
        user_id = int(subject)
    except jwt.ExpiredSignatureError:
        raise UnauthorizedException("Access token has expired")
    except (jwt.PyJWTError, TypeError, ValueError):
        raise UnauthorizedException("Invalid access token")

    user = db.scalar(select(User).where(User.id == user_id))
    if user is None:
        raise UnauthorizedException("User not found")
    if not user.is_active:
        raise ForbiddenException("User account is inactive")

    return user


def get_current_admin_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.role != UserRole.ADMIN:
        raise ForbiddenException()

    return current_user
