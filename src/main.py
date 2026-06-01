import os
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from decimal import Decimal

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.db import engine
from src.models import Base
from src.routers import router as main_router
from src.auth import router as auth
from src.auth.security import security


# Современный подход с lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Запускается при старте и завершении приложения"""
    # Код при старте (бывший on_event("startup"))
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield  # Здесь приложение работает

    # Код при завершении (бывший on_event("shutdown"))
    # Например: закрытие соединений, очистка ресурсов
    await engine.dispose()


# Создаем приложение с lifespan
app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(main_router)
app.include_router(auth.router)

security.handle_errors(app)