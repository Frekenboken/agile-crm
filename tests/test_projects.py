import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestProjectManagement:
    """Сценарий 2 – Управление проектом"""

    async def test_create_project_as_admin(self, client: AsyncClient, test_users, test_organisation):
        """Создание проекта от имени Admin"""
        # Логинимся как admin
        await client.post("/auth/login", json={
            "email": test_users["admin"]["email"],
            "password": test_users["admin"]["password"]
        })

        response = await client.post("/projects", json={
            "name": "New Project",
            "description": "Test project",
            "organisation_id": test_organisation.id
        })

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "New Project"

    async def test_add_member_to_project(self, client: AsyncClient, test_users, test_project):
        """Добавление участника в проект"""
        # Логинимся как admin
        await client.post("/auth/login", json={
            "email": test_users["admin"]["email"],
            "password": test_users["admin"]["password"]
        })

        # Создаем нового пользователя
        await client.post("/auth/register", json={
            "email": "newmember@test.com",
            "first_name": "New",
            "last_name": "Member",
            "password": "pass123"
        })

        # Получаем его ID
        await client.post("/auth/login", json={
            "email": "newmember@test.com",
            "password": "pass123"
        })
        me_response = await client.get("/auth/me")
        new_user_id = me_response.json()["id"]

        # Логинимся обратно как admin
        await client.post("/auth/login", json={
            "email": test_users["admin"]["email"],
            "password": test_users["admin"]["password"]
        })

        # Добавляем в проект
        response = await client.post(
            f"/projects/{test_project.id}/members/{new_user_id}"
        )

        assert response.status_code == 200
        data = response.json()
        assert str(data["project_id"]) == str(test_project.id)

    async def test_get_project(self, client: AsyncClient, test_users, test_project):
        """Просмотр проекта"""
        # Логинимся как developer
        await client.post("/auth/login", json={
            "email": test_users["dev"]["email"],
            "password": test_users["dev"]["password"]
        })

        response = await client.get(f"/projects/{test_project.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == test_project.name