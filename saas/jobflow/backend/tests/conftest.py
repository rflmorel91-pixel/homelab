from collections.abc import Generator
import os

import pytest
from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import Session, sessionmaker
from fastapi.testclient import TestClient



POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")

if not POSTGRES_PASSWORD:
    raise RuntimeError(
        "POSTGRES_PASSWORD environment variable is required for tests"
    )

TEST_DATABASE_URL = (
    f"postgresql+psycopg://jobflow:{POSTGRES_PASSWORD}"
    "@127.0.0.1:5433/jobflow_test"
)
os.environ["DATABASE_URL"] = TEST_DATABASE_URL
os.environ["JWT_SECRET"] = "jobflow-test-jwt-secret-at-least-32-bytes"

from app.database import Base, get_db
from app.main import app
from app.models import Tenant, TenantMembership, User

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
                "password_reset_tokens, admin_audit_logs, "
                "user_invitations, payments, "
                "invoices, schedules, "
                "estimates, jobs, customers, tenant_memberships, "
                "users, tenants, leads, products "
                "RESTART IDENTITY CASCADE"
            )
        )

        connection.execute(
            text(
                """
                INSERT INTO products
                    (name, slug, status, workspace_key, created_at)
                VALUES
                    (
                        'JobFlow',
                        'jobflow',
                        'active',
                        'jobflow',
                        CURRENT_TIMESTAMP
                    )
                """
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

            product_id=1,
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

    from app.security import create_access_token

    with TestClient(
        app,
        headers={
            "Authorization": f"Bearer {create_access_token(user_id)}",
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

    with TestClient(app, base_url="https://testserver") as test_client:
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

        from app.security import create_access_token

        return {
            "Authorization": f"Bearer {create_access_token(user.id)}",
            "X-Tenant-ID": str(tenant.id),
        }

    client.auth_user = user
    client.auth_headers = headers

    return client
