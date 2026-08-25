from io import BytesIO

from conftest import register_and_login


def auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_auth_project_task_happy_path(client):
    token = register_and_login(client, "owner@example.com")

    project = client.post(
        "/projects",
        headers=auth(token),
        json={"name": "Integration project", "description": "Test project"},
    )
    assert project.status_code == 201
    project_id = project.json()["id"]

    task = client.post(
        f"/projects/{project_id}/tasks",
        headers=auth(token),
        json={"title": "Test task", "priority": "HIGH"},
    )
    assert task.status_code == 201
    task_id = task.json()["id"]

    comment = client.post(
        f"/tasks/{task_id}/comments",
        headers=auth(token),
        json={"content": "A valid comment"},
    )
    assert comment.status_code == 201

    attachment = client.post(
        f"/tasks/{task_id}/attachments",
        headers=auth(token),
        files={"file": ("notes.txt", BytesIO(b"hello"), "text/plain")},
    )
    assert attachment.status_code == 201
    assert attachment.json()["filename"] == "notes.txt"


def test_validation_and_auth_errors_never_return_500(client):
    duplicate_email = "duplicate@example.com"
    register_and_login(client, duplicate_email)

    duplicate = client.post(
        "/auth/register",
        json={"email": duplicate_email, "password": "Password@123", "full_name": "Duplicate"},
    )
    assert duplicate.status_code == 400
    assert duplicate.status_code != 500

    invalid_login = client.post(
        "/auth/login",
        data={"email": duplicate_email, "password": "wrong"},
    )
    assert invalid_login.status_code == 422

    unauthenticated = client.get("/projects")
    assert unauthenticated.status_code == 401


def test_project_membership_and_attachment_errors(client):
    owner_token = register_and_login(client, "second-owner@example.com")
    member_token = register_and_login(client, "member@example.com")

    project = client.post(
        "/projects",
        headers=auth(owner_token),
        json={"name": "Permission project"},
    )
    project_id = project.json()["id"]

    member_id = client.get("/users/me", headers=auth(member_token)).json()["id"]
    add_member = client.post(
        f"/projects/{project_id}/members",
        headers=auth(owner_token),
        json={"user_id": member_id},
    )
    assert add_member.status_code == 201

    forbidden_update = client.patch(
        f"/projects/{project_id}",
        headers=auth(member_token),
        json={"name": "Should fail"},
    )
    assert forbidden_update.status_code == 403

    invalid_file = client.post(
        "/tasks/999999/attachments",
        headers=auth(owner_token),
        files={"file": ("malware.exe", BytesIO(b"bad"), "application/octet-stream")},
    )
    assert invalid_file.status_code == 404
    assert invalid_file.status_code != 500

    missing_project_tasks = client.get(
        "/projects/999999/tasks",
        headers=auth(owner_token),
    )
    assert missing_project_tasks.status_code == 404
