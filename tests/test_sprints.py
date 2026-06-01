import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestSprintManagement:
    """Сценарий 4 – Управление спринтом"""

    async def test_create_sprint(self, client: AsyncClient, test_users, test_project):
        """Создание спринта"""
        # Логинимся как scrum master
        await client.post("/auth/login", json={
            "email": test_users["scrum"]["email"],
            "password": test_users["scrum"]["password"]
        })

        response = await client.post("/sprints", json={
            "name": "Sprint 2",
            "goal": "Complete features",
            "project_id": str(test_project.id)
        })

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Sprint 2"
        assert data["is_active"] == False

    async def test_sprint_lifecycle(self, client: AsyncClient, test_users, test_sprint, test_project):
        """Полный цикл жизни спринта: создание → запуск → завершение"""
        # Логинимся как scrum master
        await client.post("/auth/login", json={
            "email": test_users["scrum"]["email"],
            "password": test_users["scrum"]["password"]
        })

        # Запускаем спринт
        start_response = await client.post(f"/project/{test_project.id}/sprints/{test_sprint.id}/start")
        assert start_response.status_code == 200
        assert start_response.json()["is_active"] == True

        # Завершаем спринт
        complete_response = await client.post(f"/project/{test_project.id}/sprints/{test_sprint.id}/complete")
        assert complete_response.status_code == 200
        assert complete_response.json()["is_completed"] == True

    async def test_only_one_active_sprint(self, client: AsyncClient, test_users, test_project, test_sprint):
        """Нельзя иметь два активных спринта одновременно"""
        client.cookies.clear()
        await client.post("/auth/login", json={
            "email": test_users["scrum"]["email"],
            "password": test_users["scrum"]["password"]
        })

        # Запускаем первый спринт
        start_response = await client.post(f"/project/{test_project.id}/sprints/{test_sprint.id}/start")
        assert start_response.status_code == 200
        assert start_response.json()["is_active"] == True

        # Создаем второй спринт
        create_response = await client.post("/sprints", json={
            "name": "Sprint 2",
            "goal": "Second sprint",
            "project_id": str(test_project.id)
        })
        assert create_response.status_code == 200
        sprint2_id = create_response.json()["id"]

        # Пытаемся запустить второй спринт (должен вернуть ошибку)
        start_response2 = await client.post(f"/project/{test_project.id}/sprints/{sprint2_id}/start")
        assert start_response2.status_code in [400, 409, 422]

        # Завершаем первый спринт
        await client.post(f"/project/{test_project.id}/sprints/{test_sprint.id}/complete")

        # Теперь можно запустить второй
        start_response3 = await client.post(f"/project/{test_project.id}/sprints/{sprint2_id}/start")
        assert start_response3.status_code == 200
        assert start_response3.json()["is_active"] == True

    async def test_view_sprints(self, client: AsyncClient, test_users, test_project):
        """Просмотр спринтов проекта"""
        # Логинимся как developer
        await client.post("/auth/login", json={
            "email": test_users["dev"]["email"],
            "password": test_users["dev"]["password"]
        })

        response = await client.get(f"/sprints?project_id={test_project.id}")

        assert response.status_code == 200
        assert isinstance(response.json(), list)
