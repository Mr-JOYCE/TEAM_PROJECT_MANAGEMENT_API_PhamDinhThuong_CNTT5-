from datetime import datetime, timedelta

import bcrypt

from app.db.database import SessionLocal
from app.models.user import User
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.task import Task


def hash_password(password: str) -> str:
    return bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")


def seed_database():
    db = SessionLocal()

    try:

        admin = User(
            email="admin@example.com",
            password_hash=hash_password("Admin@123"),
            full_name="System Administrator",
            role="ADMIN",
            is_active=True,
        )

        user1 = User(
            email="nguyenan@example.com",
            password_hash=hash_password("User@123"),
            full_name="Nguyen An",
            role="USER",
            is_active=True,
        )

        user2 = User(
            email="tranbinh@example.com",
            password_hash=hash_password("User@123"),
            full_name="Tran Binh",
            role="USER",
            is_active=True,
        )

        user3 = User(
            email="levan@example.com",
            password_hash=hash_password("User@123"),
            full_name="Le Van",
            role="USER",
            is_active=True,
        )

        db.add_all([
            admin,
            user1,
            user2,
            user3
        ])

        db.flush()

        project1 = Project(
            name="Project Management API",
            description="Xây dựng hệ thống quản lý dự án bằng FastAPI",
            owner_id=admin.id,
        )

        project2 = Project(
            name="E-Commerce API",
            description="API quản lý hệ thống bán hàng",
            owner_id=user1.id,
        )

        db.add_all([
            project1,
            project2
        ])

        db.flush()

        members = [
            ProjectMember(
                project_id=project1.id,
                user_id=admin.id,
                role="OWNER",
            ),

            ProjectMember(
                project_id=project1.id,
                user_id=user1.id,
                role="MEMBER",
            ),

            ProjectMember(
                project_id=project1.id,
                user_id=user2.id,
                role="MEMBER",
            ),

            ProjectMember(
                project_id=project2.id,
                user_id=user1.id,
                role="OWNER",
            ),

            ProjectMember(
                project_id=project2.id,
                user_id=user3.id,
                role="MEMBER",
            ),
        ]

        db.add_all(members)

        now = datetime.now()

        tasks = [
            Task(
                project_id=project1.id,
                title="Thiết kế database",
                description="Thiết kế users, projects, project_members và tasks",
                assignee_id=user1.id,
                status="DONE",
                priority="HIGH",
                due_date=now + timedelta(days=2),
            ),

            Task(
                project_id=project1.id,
                title="Xây dựng Authentication",
                description="Implement JWT authentication",
                assignee_id=user2.id,
                status="IN_PROGRESS",
                priority="HIGH",
                due_date=now + timedelta(days=5),
            ),

            Task(
                project_id=project1.id,
                title="Viết API Project",
                description="CRUD project",
                assignee_id=user1.id,
                status="TODO",
                priority="MEDIUM",
                due_date=now + timedelta(days=7),
            ),

            Task(
                project_id=project1.id,
                title="Viết API Task",
                description="CRUD task",
                assignee_id=user2.id,
                status="TODO",
                priority="MEDIUM",
                due_date=now + timedelta(days=10),
            ),

            Task(
                project_id=project2.id,
                title="Thiết kế Product API",
                description="Xây dựng API quản lý sản phẩm",
                assignee_id=user3.id,
                status="IN_PROGRESS",
                priority="HIGH",
                due_date=now + timedelta(days=4),
            ),

            Task(
                project_id=project2.id,
                title="Testing API",
                description="Kiểm thử các endpoint",
                assignee_id=user3.id,
                status="TODO",
                priority="LOW",
                due_date=now + timedelta(days=12),
            ),
        ]

        db.add_all(tasks)
        db.commit()

        print("===================================")
        print("Seed database thành công!")
        print("===================================")

        print("\nUsers:")
        print("admin@example.com / Admin@123")
        print("nguyenan@example.com / User@123")
        print("tranbinh@example.com / User@123")
        print("levan@example.com / User@123")

        print("\nProjects:")
        print("- Project Management API")
        print("- E-Commerce API")

        print("\nTasks:")
        print("- Thiết kế database")
        print("- Xây dựng Authentication")
        print("- Viết API Project")
        print("- Viết API Task")
        print("- Thiết kế Product API")
        print("- Testing API")

    except Exception as e:
        db.rollback()

        print("Seed database thất bại!")
        print(f"Lỗi: {e}")

    finally:
        db.close()


if __name__ == "__main__":
    seed_database()