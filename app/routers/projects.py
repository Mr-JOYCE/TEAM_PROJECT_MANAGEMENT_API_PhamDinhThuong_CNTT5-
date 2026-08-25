from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate
from app.schemas.project_member import ProjectMemberCreate, ProjectMemberResponse
from app.services.project_service import (
	add_member,
	create_project,
	delete_project,
	get_project,
	list_members,
	list_projects,
	remove_member,
	update_project,
)


router = APIRouter(prefix="/projects", tags=["Projects"])


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create(
	data: ProjectCreate,
	current_user: User = Depends(get_current_user),
	db: Session = Depends(get_db),
):
	return create_project(db, data, current_user)


@router.get("", response_model=list[ProjectResponse])
def list_all(
	search: str | None = Query(default=None),
	current_user: User = Depends(get_current_user),
	db: Session = Depends(get_db),
):
	return list_projects(db, current_user.id, search)


@router.get("/{project_id}", response_model=ProjectResponse)
def get_one(
	project_id: int,
	current_user: User = Depends(get_current_user),
	db: Session = Depends(get_db),
):
	return get_project(db, project_id, current_user.id)


@router.patch("/{project_id}", response_model=ProjectResponse)
@router.put("/{project_id}", response_model=ProjectResponse, include_in_schema=False)
def update(
	project_id: int,
	data: ProjectUpdate,
	current_user: User = Depends(get_current_user),
	db: Session = Depends(get_db),
):
	return update_project(db, project_id, data, current_user)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete(
	project_id: int,
	current_user: User = Depends(get_current_user),
	db: Session = Depends(get_db),
):
	delete_project(db, project_id, current_user)
	return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{project_id}/members", response_model=ProjectMemberResponse, status_code=status.HTTP_201_CREATED)
def add_project_member(
	project_id: int,
	data: ProjectMemberCreate,
	current_user: User = Depends(get_current_user),
	db: Session = Depends(get_db),
):
	return add_member(db, project_id, data.user_id, current_user)


@router.delete("/{project_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project_member(
	project_id: int,
	user_id: int,
	current_user: User = Depends(get_current_user),
	db: Session = Depends(get_db),
):
	remove_member(db, project_id, user_id, current_user)
	return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{project_id}/members", response_model=list[ProjectMemberResponse])
def get_project_members(
	project_id: int,
	current_user: User = Depends(get_current_user),
	db: Session = Depends(get_db),
):
	return list_members(db, project_id, current_user.id)
