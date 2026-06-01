import asyncio
from typing import AsyncGenerator, Dict
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool

from src.main import app
from src.core.db import get_session
from src.models import Base
import src.crud as crud
from src.schemas import (
    UserCreate, OrganisationCreate, ProjectCreate,
    SprintCreate, TaskCreate, ProjectMemberCreate,
    TaskParticipantCreate, OrganisationMemberCreate
)
from src.models import (
    OrganisationRole, ProjectRole, ParticipantRole,
    TaskType, TaskPriority
)

# Тестовая БД SQLite в памяти
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestSessionLocal = async_sessionmaker(
    test_engine,
    expire_on_commit=False,
    class_=AsyncSession
)


async def override_get_session() -> AsyncGenerator[AsyncSession, None]:
    async with TestSessionLocal() as session:
        yield session


app.dependency_overrides[get_session] = override_get_session


@pytest_asyncio.fixture(scope="function")
async def db_session():
    """Создает чистую БД для каждого теста"""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with TestSessionLocal() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture(scope="function")
async def client() -> AsyncGenerator[AsyncClient, None]:
    """HTTP клиент для тестов с поддержкой кук"""
    transport = ASGITransport(app=app)
    async with AsyncClient(
            transport=transport,
            base_url="http://test",
            cookies={}  # Куки будут храниться здесь
    ) as ac:
        yield ac


# ФИКСТУРЫ ДЛЯ ТЕСТОВЫХ ДАННЫХ

@pytest_asyncio.fixture
async def test_users(db_session, client) -> Dict[str, dict]:
    """
    Создает пользователей: admin, scrum, dev
    """
    users = {}

    # Admin/Product Owner
    await client.post("/auth/register", json={
        "email": "admin@test.com",
        "first_name": "Admin",
        "last_name": "User",
        "password": "admin123"
    })

    # Scrum Master
    await client.post("/auth/register", json={
        "email": "scrum@test.com",
        "first_name": "Scrum",
        "last_name": "Master",
        "password": "scrum123"
    })

    # Developer
    await client.post("/auth/register", json={
        "email": "dev@test.com",
        "first_name": "Dev",
        "last_name": "Eloper",
        "password": "dev123"
    })

    users["admin"] = {"email": "admin@test.com", "password": "admin123"}
    users["scrum"] = {"email": "scrum@test.com", "password": "scrum123"}
    users["dev"] = {"email": "dev@test.com", "password": "dev123"}

    # Получаем объекты пользователей через БД
    for role in users:
        user = await crud.get_user_by_email(db_session, users[role]["email"])
        users[role]["id"] = str(user.id)

    return users


@pytest_asyncio.fixture
async def test_organisation(db_session, test_users):
    """Создает тестовую организацию"""
    organisation_data = OrganisationCreate(name="Test Organisation")
    org = await crud.create_organisation(db_session, organisation_data)

    # Добавляем всех в организацию
    await crud.add_user_to_organisation(db_session, OrganisationMemberCreate(
        organisation_id=org.id,
        user_id=test_users["admin"]["id"],
        role=OrganisationRole.owner
    ))

    for role in ["scrum", "dev"]:
        await crud.add_user_to_organisation(db_session, OrganisationMemberCreate(
            organisation_id=org.id,
            user_id=test_users[role]["id"],
            role=OrganisationRole.member
        ))

    return org


@pytest_asyncio.fixture
async def test_project(db_session, test_organisation, test_users):
    """Создает тестовый проект с командой"""
    project_data = ProjectCreate(
        name="Test Project",
        description="Project for testing",
        organisation_id=test_organisation.id
    )
    project = await crud.create_project(db_session, project_data)

    # Product Owner
    await crud.add_user_to_project(db_session, ProjectMemberCreate(
        project_id=project.id,
        user_id=test_users["admin"]["id"],
        role=ProjectRole.product_owner
    ))

    # Scrum Master
    await crud.add_user_to_project(db_session, ProjectMemberCreate(
        project_id=project.id,
        user_id=test_users["scrum"]["id"],
        role=ProjectRole.scrum_master
    ))

    # Developer
    await crud.add_user_to_project(db_session, ProjectMemberCreate(
        project_id=project.id,
        user_id=test_users["dev"]["id"],
        role=ProjectRole.developer
    ))

    return project


@pytest_asyncio.fixture
async def test_sprint(db_session, test_project):
    """Создает тестовый спринт"""
    sprint_data = SprintCreate(
        name="Sprint 1",
        goal="First sprint",
        project_id=test_project.id
    )
    return await crud.create_sprint(db_session, sprint_data)


@pytest_asyncio.fixture
async def test_task(db_session, test_project, test_sprint, test_users):
    """Создает тестовую задачу"""
    task_data = TaskCreate(
        title="Test Task",
        description="Task for testing",
        type=TaskType.task,
        priority=TaskPriority.high,
        story_points=5,
        project_id=test_project.id,
        sprint_id=test_sprint.id,
        reporter_id=test_users["scrum"]["id"]
    )
    task = await crud.create_task(db_session, task_data)

    # Назначаем разработчика как worker
    await crud.add_participant_to_task(db_session, TaskParticipantCreate(
        task_id=task.id,
        user_id=test_users["dev"]["id"],
        role=ParticipantRole.worker
    ))

    return task


# Вспомогательная функция для логина (JWT сохраняется в куках)
async def login_user(client: AsyncClient, email: str, password: str) -> dict:
    """Логинит пользователя и возвращает данные ответа"""
    response = await client.post("/auth/login", json={
        "email": email,
        "password": password
    })
    return response.json()