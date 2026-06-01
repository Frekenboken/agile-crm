import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestAuthentication:
    """Сценарий 1 – Аутентификация"""

    async def test_register_user(self, client: AsyncClient):
        """Регистрация нового пользователя"""
        response = await client.post("/auth/register", json={
            "email": "testuser@test.com",
            "first_name": "Test",
            "last_name": "User",
            "password": "secret123"
        })

        assert response.status_code == 201
        data = response.json()["user"]
        assert data["email"] == "testuser@test.com"
        assert "password" not in data

    async def test_login_get_token_in_cookies(self, client: AsyncClient, test_users):
        """Авторизация и получение JWT в куках"""
        response = await client.post("/auth/login", json={
            "email": test_users["admin"]["email"],
            "password": test_users["admin"]["password"]
        })

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data

        # Проверяем, что кука установилась
        assert "access_token_cookie" in response.cookies or "access_token_cookie" in client.cookies

    async def test_access_protected_route_with_cookie(self, client: AsyncClient, test_users):
        """Доступ к защищенному ресурсу с кукой"""
        # Логинимся (кука сохраняется автоматически)
        await client.post("/auth/login", json={
            "email": test_users["dev"]["email"],
            "password": test_users["dev"]["password"]
        })

        # Запрашиваем защищенный ресурс
        response = await client.get("/auth/me")

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_users["dev"]["email"]

    async def test_access_without_auth(self, client: AsyncClient):
        """Доступ без авторизации"""
        response = await client.get("/auth/me")
        assert response.status_code == 401

    async def test_login_wrong_password(self, client, test_users):
        response = await client.post("/auth/login", json={
            "email": test_users["admin"]["email"],
            "password": "wrongpassword"
        })
        assert response.status_code == 401