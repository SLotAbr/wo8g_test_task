import asyncio
from typing import Any, Generator
import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.models import Base
from src.database import get_async_session
from src.app import create_app
from src.config import config


@pytest.fixture(scope="session")
def event_loop(request) -> Generator:
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncSession:
    async_engine = create_async_engine(config.TEST_DATABASE_URL)
    AsyncSessionFactory = sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)

    async with AsyncSessionFactory() as session:
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        yield session

    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await async_engine.dispose()


@pytest.fixture(scope="session")
def app() -> Generator[FastAPI, Any, None]:
    app = create_app()
    
    yield app


@pytest_asyncio.fixture(scope="function")
async def client(app: FastAPI, db_session) -> AsyncClient:
    async def _get_session():
        return db_session

    app.dependency_overrides[get_async_session] = _get_session
    
    async with AsyncClient(transport=ASGITransport(app), base_url="http://test") as client:
        yield client
    
    app.dependency_overrides.clear()


