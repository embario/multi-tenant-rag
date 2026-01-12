import os
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db.base import Base
from app.db.deps import get_db

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql+psycopg://postgres:postgres@db:5432/rag"
)


@pytest.fixture(scope="session")
def engine():
    engine = create_engine(DATABASE_URL)
    return engine


@pytest.fixture(scope="session", autouse=True)
def create_test_schema(engine):
    # Create tables once for the test session.
    # If you use Alembic migrations in tests, remove this and run migrations instead.
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(engine):
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def client(db_session):
    def _get_db_override():
        yield db_session

    app.dependency_overrides[get_db] = _get_db_override
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture(scope="session")
def tenant_ids(engine):
    tenants = {
        "tenant_a": uuid.UUID("00000000-0000-0000-0000-000000000001"),
        "tenant_b": uuid.UUID("00000000-0000-0000-0000-000000000002"),
    }

    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        from app.db.models import Tenant

        for name, tenant_id in tenants.items():
            if not session.get(Tenant, tenant_id):
                session.add(Tenant(id=tenant_id, name=name))
        session.commit()
    finally:
        session.close()

    return tenants


@pytest.fixture(autouse=True)
def upload_dir(tmp_path, monkeypatch):
    path = tmp_path / "uploads"
    path.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("UPLOAD_DIR", str(path))
    return path
