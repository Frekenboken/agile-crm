import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestTaskManagement:
    """Сценарий 5 – Управление задачами и проверка статусов"""

    async def test_create_task(self, client: AsyncClient, test_users, test_project, test_sprint):
        """Создание задачи"""
        await client.post("/auth/login", json={
            "email": test_users["scrum"]["email"],
            "password": test_users["scrum"]["password"]
        })

        response = await client.post(f"/projects/{test_project.id}/tasks", json={
            "title": "User Story",
            "description": "As a user...",
            "type": "story",
            "priority": "high",
            "story_points": 5,
            "project_id": str(test_project.id),
            "sprint_id": str(test_sprint.id)
        })

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "User Story"
        assert data["priority"] == "high"

    async def test_change_task_status_flow(self, client: AsyncClient, test_users, test_project, test_sprint):
        """Смена статусов задачи и блокировка недопустимого перехода"""
        # Логинимся как scrum master и создаем задачу
        await client.post("/auth/login", json={
            "email": test_users["scrum"]["email"],
            "password": test_users["scrum"]["password"]
        })

        task_response = await client.post(f"/projects/{test_project.id}/tasks", json={
            "title": "Status Test Task",
            "project_id": str(test_project.id),
            "sprint_id": str(test_sprint.id)
        })
        task_id = task_response.json()["id"]

        # Назначаем разработчика
        await client.post(f"/projects/{test_project.id}/tasks/{task_id}/members/{test_users['dev']['id']}")

        # Логинимся как developer
        await client.post("/auth/login", json={
            "email": test_users["dev"]["email"],
            "password": test_users["dev"]["password"]
        })

        # To Do → In Progress
        response1 = await client.patch(
            f"/projects/{test_project.id}/tasks/{task_id}",
            json={"status": "in_progress"}
        )
        assert response1.status_code == 200
        assert response1.json()["status"] == "in_progress"

        # In Progress → Review
        response2 = await client.patch(
            f"/projects/{test_project.id}/tasks/{task_id}",
            json={"status": "review"}
        )
        assert response2.status_code == 200
        assert response2.json()["status"] == "review"

        # Review → Testing
        response3 = await client.patch(
            f"/projects/{test_project.id}/tasks/{task_id}",
            json={"status": "testing"}
        )
        assert response3.status_code == 200
        assert response3.json()["status"] == "testing"

        # Testing → Done
        response4 = await client.patch(
            f"/projects/{test_project.id}/tasks/{task_id}",
            json={"status": "done"}
        )
        assert response4.status_code == 200
        assert response4.json()["status"] == "done"

        # Попытка недопустимого перехода Done → To Do
        response5 = await client.patch(
            f"/projects/{test_project.id}/tasks/{task_id}",
            json={"status": "todo"}
        )
        assert response5.status_code in [400, 422]

    async def test_add_comment_to_task(self, client: AsyncClient, test_users, test_project, test_task):
        """Добавление комментария к задаче"""
        await client.post("/auth/login", json={
            "email": test_users["dev"]["email"],
            "password": test_users["dev"]["password"]
        })

        response = await client.post(
            f"/projects/{test_project.id}/tasks/{test_task.id}/comments",
            json={"content": "Working on this task"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["content"] == "Working on this task"

    async def test_view_project_tasks(self, client: AsyncClient, test_users, test_project):
        """Просмотр задач проекта"""
        await client.post("/auth/login", json={
            "email": test_users["dev"]["email"],
            "password": test_users["dev"]["password"]
        })

        response = await client.get(f"/projects/{test_project.id}/tasks")

        assert response.status_code == 200
        assert isinstance(response.json(), list)