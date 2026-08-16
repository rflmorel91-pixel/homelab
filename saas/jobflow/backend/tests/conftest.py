from collections.abc import Generator

import pytest
from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import Session, sessionmaker
from fastapi.testclient import TestClient

from app.database import Base, get_db
from app.main import app
from app.models import Tenant, TenantMembership, User


TEST_DATABASE_URL = (
    "postgresql+psycopg://jobflow:jobflow_dev_password"
    "@127.0.0.1:5433/jobflow_test"
)

test_engine = create_engine(
    TEST_DATABASE_URL,
    pool_pre_ping=True,
)

TestingSessionLocal = sessionmaker(
    bind=test_engine,
    autoflush=False,
    autocommit=False,
)


@pytest.fixture(autouse=True)
def clean_test_database():
    with test_engine.begin() as connection:
        connection.execute(
            text(
                "TRUNCATE TABLE "
                "payments, invoices, schedules, estimates, jobs, "
                "customers, tenant_memberships, users, tenants "
                "RESTART IDENTITY CASCADE"
            )
        )


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    session = TestingSessionLocal()

    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    def override_get_db():
        db = TestingSessionLocal()

        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    db = TestingSessionLocal()

    try:
        user = User(
            email="default-test-user@example.com",
            display_name="Default Test User",
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        tenant = Tenant(
            name="Default Test Tenant",
            slug="default-test-tenant",
        )
        db.add(tenant)
        db.commit()
        db.refresh(tenant)

        membership = TenantMembership(
            tenant_id=tenant.id,
            user_id=user.id,
            role="member",
        )
        db.add(membership)
        db.commit()

        user_id = user.id
        tenant_id = tenant.id
    finally:
        db.close()

    with TestClient(
        app,
        headers={
            "X-User-ID": str(user_id),
            "X-Tenant-ID": str(tenant_id),
        },
    ) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def raw_client() -> Generator[TestClient, None, None]:
    def override_get_db():
        db = TestingSessionLocal()

        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def authenticated_client(client, db_session):
    from app.models import Tenant, TenantMembership, User

    user = User(
        email="test-user@example.com",
        display_name="Test User",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    def headers(tenant):
        existing = db_session.scalar(
            select(TenantMembership).where(
                TenantMembership.tenant_id == tenant.id,
                TenantMembership.user_id == user.id,
            )
        )

        if existing is None:
            membership = TenantMembership(
                tenant_id=tenant.id,
                user_id=user.id,
                role="member",
            )
            db_session.add(membership)
            db_session.commit()

        return {
            "X-User-ID": str(user.id),
            "X-Tenant-ID": str(tenant.id),
        }

    client.auth_user = user
    client.auth_headers = headers

    return client
