import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool
from unittest.mock import patch

from app.main import create_app
from app.core.database import get_db_session
from app.models import Base
from app.core.config import Settings, get_settings


TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def test_settings():
    return Settings(
        database_url=TEST_DATABASE_URL,
        debug=True,
        environment="test",
        session_secret_key="test-secret-key-for-testing-only",
        demo_mode=True,
    )


@pytest.fixture(scope="session")
async def test_engine(test_settings):
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture(scope="function")
async def test_session(test_engine):
    async_session = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )
    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.fixture(scope="function")
async def client(test_session, test_settings):
    def override_get_db():
        yield test_session

    app = create_app()
    app.dependency_overrides[get_db_session] = override_get_db
    
    def override_get_settings():
        return test_settings
    
    with patch("app.core.config.get_settings", override_get_settings):
        with patch("app.core.auth.get_settings", override_get_settings):
            with patch("app.core.database.get_settings", override_get_settings):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as ac:
                    yield ac


@pytest.fixture
def auth_headers():
    return {"Cookie": "session=demo-token"}


@pytest_asyncio.fixture
async def demo_user_client(client):
    response = await client.get("/api/v1/auth/demo-login")
    assert response.status_code == 200
    cookie = response.headers.get("set-cookie", "")
    return client, cookie