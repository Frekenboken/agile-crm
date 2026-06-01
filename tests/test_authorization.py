import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestAuthorization:
    """Сценарий 6 – Проверка авторизации"""

    async def test_developer_cannot_create_task(self, client: AsyncClient, test_users, test_project):
        """Developer не может создать задачу"""
        await client.post("/auth/login", json={
            "email": test_users["dev"]["email"],
            "password": test_users["dev"]["password"]
        })

        response = await client.post(f"/projects/{test_project.id}/tasks", json={
            "title": "Unauthorized Task",
            "project_id": str(test_project.id)
        })

        assert response.status_code == 403

    async def test_developer_cannot_delete_task(self, client: AsyncClient, test_users, test_project, test_task):
        """Developer не может удалить задачу"""
        await client.post("/auth/login", json={
            "email": test_users["dev"]["email"],
            "password": test_users["dev"]["password"]
        })

        response = await client.delete(f"/projects/{test_project.id}/tasks/{test_task.id}")

        assert response.status_code == 403

    async def test_developer_cannot_create_sprint(self, client: AsyncClient, test_users, test_project):
        """Developer не может создать спринт"""
        await client.post("/auth/login", json={
            "email": test_users["dev"]["email"],
            "password": test_users["dev"]["password"]
        })

        response = await client.post("/sprints", json={
            "name": "Unauthorized Sprint",
            "project_id": str(test_project.id)
        })

        assert response.status_code == 403

    async def test_unauthorized_access(self, client: AsyncClient, test_project):
        """Доступ без авторизации"""
        client.cookies.clear()
        response = await client.get(f"/projects/{test_project.id}")
        assert response.status_code == 401
