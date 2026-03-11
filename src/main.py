import os
from datetime import datetime, timedelta
from decimal import Decimal

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.db import engine
from src.models import Base, UserRole
from src.routers import user, task, sprint, project, project_member
from src.auth import router as auth

from src.auth.security import security
# from src.schemas.driver import DriverCreate
# from src.schemas.user import UserCreate, UserUpdate

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user.router)
app.include_router(task.router)
app.include_router(sprint.router)
app.include_router(project.router)
app.include_router(project_member.router)
app.include_router(auth.router)

security.handle_errors(app)

@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)