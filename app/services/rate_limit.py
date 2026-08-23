from datetime import datetime, timedelta, timezone
from threading import Lock

from app.core.config import settings
from app.exceptions.error import TooManyRequestsException


_failed_attempts: dict[str, tuple[int, datetime]] = {}
_lock = Lock()


def ensure_login_allowed(key: str) -> None:
	with _lock:
		attempt_data = _failed_attempts.get(key)
		if attempt_data is None:
			return

		attempts, blocked_until = attempt_data
		now = datetime.now(timezone.utc)
		if blocked_until > now:
			retry_after = max(1, int((blocked_until - now).total_seconds()))
			raise TooManyRequestsException(retry_after)
		if attempts >= settings.LOGIN_MAX_ATTEMPTS:
			del _failed_attempts[key]


def record_login_failure(key: str) -> None:
	with _lock:
		attempts, _ = _failed_attempts.get(key, (0, datetime.now(timezone.utc)))
		attempts += 1
		blocked_until = datetime.now(timezone.utc)
		if attempts >= settings.LOGIN_MAX_ATTEMPTS:
			blocked_until += timedelta(minutes=settings.LOGIN_BLOCK_MINUTES)
		_failed_attempts[key] = (attempts, blocked_until)


def reset_login_attempts(key: str) -> None:
	with _lock:
		_failed_attempts.pop(key, None)
