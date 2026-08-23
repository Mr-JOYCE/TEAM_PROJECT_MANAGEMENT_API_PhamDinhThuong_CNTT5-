from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.user import User


def get_users(
	db: Session,
	search: str | None = None,
	is_active: bool | None = None,
) -> list[User]:
	query = select(User).order_by(User.id)

	if search:
		search_pattern = f"%{search.strip()}%"
		query = query.where(
			or_(
				User.full_name.ilike(search_pattern),
				User.email.ilike(search_pattern),
			)
		)

	if is_active is not None:
		query = query.where(User.is_active == is_active)

	return list(db.scalars(query).all())
