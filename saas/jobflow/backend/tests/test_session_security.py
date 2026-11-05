"""Real auth routes/JWTs with isolated SQLite users; no production services.

Run without PostgreSQL: python -B tests/test_session_security.py
The normal PostgreSQL suite also collects these checks.
"""
from datetime import datetime, timedelta, timezone
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

if __name__ == "__main__":
    os.environ["DATABASE_URL"] = "sqlite://"
    os.environ["JWT_SECRET"] = "synthetic-session-regression-secret-32-bytes"
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
import jwt
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.api.auth import router
from app.auth_context import get_current_user_id
from app.database import get_db
from app.models import User
from app.security import (
    ABSOLUTE_SESSION_LIFETIME_SECONDS,
    JWT_ALGORITHM,
    JWT_SECRET,
    create_access_token,
    hash_password,
)


class SessionSecurity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.password_hash = hash_password("synthetic-session-password")

    def setUp(self):
        self.now = datetime.now(timezone.utc).replace(microsecond=0)
        clock = self

        class Clock(datetime):
            @classmethod
            def now(cls, tz=None):
                return clock.now.astimezone(tz) if tz else clock.now.replace(tzinfo=None)

        for target in ("app.security.datetime", "jwt.api_jwt.datetime"):
            patcher = patch(target, Clock)
            patcher.start()
            self.addCleanup(patcher.stop)

        self.engine = create_engine(
            "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool,
        )
        User.__table__.create(self.engine)
        self.db = Session(self.engine)
        self.user = User(
            email="session@example.test", display_name="Synthetic session owner",
            password_hash=self.password_hash, is_active=True,
        )
        self.db.add(self.user)
        self.db.commit()
        app = FastAPI()
        app.include_router(router, prefix="/api/v1")
        app.dependency_overrides[get_db] = lambda: self.db

        @app.get("/protected")
        def protected(user_id: int = Depends(get_current_user_id)):
            return {"user_id": user_id}

        self.client = TestClient(app, base_url="https://testserver")
        self.addCleanup(self.engine.dispose)
        self.addCleanup(self.db.close)
        self.addCleanup(self.client.close)

    def login(self):
        response = self.client.post("/api/v1/auth/login", json={
            "email": self.user.email, "password": "synthetic-session-password",
        })
        self.assertEqual(response.status_code, 200, response.text)
        return response.cookies["jobflow_access_token"]

    def access(self, token, *, bearer=False):
        self.client.cookies.clear()
        headers = ({"Authorization": f"Bearer {token}"} if bearer else
                   {"Cookie": f"jobflow_access_token={token}"})
        return self.client.get("/protected", headers=headers)

    def claims(self, token):
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])

    def signed(self, **changes):
        payload = self.claims(create_access_token(self.user.id))
        payload.update(changes)
        return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    def test_logout_revokes_original_renewed_and_other_device_tokens(self):
        first = self.login()
        self.now += timedelta(seconds=10)
        renewed = self.access(first).cookies["jobflow_access_token"]
        self.now += timedelta(seconds=10)
        other_device = self.login()
        response = self.client.post("/api/v1/auth/logout")
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("jobflow_access_token", self.client.cookies)
        self.db.refresh(self.user)
        self.assertEqual(self.user.session_version, 1)
        for token in (first, renewed, other_device):
            for bearer in (False, True):
                with self.subTest(token=token[-8:], bearer=bearer):
                    denied = self.access(token, bearer=bearer)
                    self.assertEqual(denied.status_code, 401)
                    self.assertNotIn("set-cookie", denied.headers)
        fresh = self.login()
        self.assertEqual(self.access(fresh).status_code, 200)

    def test_bearer_logout_revokes_copied_cookie(self):
        token = self.login()
        self.client.cookies.clear()
        response = self.client.post("/api/v1/auth/logout", headers={
            "Authorization": f"Bearer {token}",
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.access(token).status_code, 401)

    def test_stale_and_anonymous_logout_do_not_revoke_fresh_login(self):
        old = self.login()
        self.client.post("/api/v1/auth/logout")
        fresh = self.login()
        self.client.cookies.clear()
        for headers in ({}, {"Cookie": f"jobflow_access_token={old}"},
                        {"Authorization": "Bearer malformed"}):
            response = self.client.post("/api/v1/auth/logout", headers=headers)
            self.assertEqual(response.status_code, 200)
            self.assertIn("Max-Age=0", response.headers["set-cookie"])
        self.db.refresh(self.user)
        self.assertEqual(self.user.session_version, 1)
        self.assertEqual(self.access(fresh).status_code, 200)

    def test_continuous_cookie_activity_cannot_extend_absolute_deadline(self):
        token = self.login()
        authenticated_at = self.claims(token)["auth_time"]
        # Exercise renewal throughout the session, rather than only a forged old token.
        for _ in range(31):
            self.now += timedelta(minutes=15)
            response = self.access(token)
            self.assertEqual(response.status_code, 200)
            token = response.cookies["jobflow_access_token"]
            self.assertEqual(self.claims(token)["auth_time"], authenticated_at)
        self.now += timedelta(minutes=14, seconds=59)
        response = self.access(token)
        self.assertEqual(response.status_code, 200)
        token = response.cookies["jobflow_access_token"]
        self.assertEqual(self.claims(token)["exp"],
                         authenticated_at + ABSOLUTE_SESSION_LIFETIME_SECONDS)
        self.assertIn("Max-Age=1", response.headers["set-cookie"])
        self.now += timedelta(seconds=1)
        for bearer in (False, True):
            self.assertEqual(self.access(token, bearer=bearer).status_code, 401)
        fresh = self.login()
        self.assertEqual(self.access(fresh).status_code, 200)

    def test_expired_absolute_age_rejected_even_with_future_jwt_expiry(self):
        old = int(self.now.timestamp()) - ABSOLUTE_SESSION_LIFETIME_SECONDS
        token = self.signed(auth_time=old)
        self.assertEqual(self.access(token).status_code, 401)

    def test_legacy_issuance_time_is_preserved_on_renewal(self):
        payload = self.claims(create_access_token(self.user.id))
        del payload["auth_time"]
        payload["iat"] -= 60
        token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        response = self.access(token)
        self.assertEqual(response.status_code, 200)
        renewed = response.cookies["jobflow_access_token"]
        self.assertEqual(self.claims(renewed)["auth_time"], payload["iat"])

    def test_malformed_authentication_time_is_rejected(self):
        for value in (None, True, "123", -1, int(self.now.timestamp()) + 1):
            with self.subTest(value=value):
                self.assertEqual(self.access(self.signed(auth_time=value)).status_code, 401)

    def test_missing_required_claims_are_rejected(self):
        for claim in ("sub", "iat", "exp"):
            payload = self.claims(create_access_token(self.user.id))
            del payload[claim]
            token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
            with self.subTest(claim=claim):
                self.assertEqual(self.access(token).status_code, 401)

    def test_idle_expiry_still_rejects_an_unused_token(self):
        token = self.login()
        self.now += timedelta(minutes=30)
        self.assertEqual(self.access(token).status_code, 401)

    def test_deadline_crossed_during_renewal_returns_401_not_500(self):
        token = self.login()
        with patch("app.auth_context.create_access_token", side_effect=jwt.InvalidTokenError):
            response = self.access(token)
        self.assertEqual(response.status_code, 401)
        self.assertNotIn("set-cookie", response.headers)

    def test_password_reset_generation_still_blocks_cookie_and_bearer(self):
        token = self.login()
        self.user.session_version += 1
        self.db.commit()
        for bearer in (False, True):
            self.assertEqual(self.access(token, bearer=bearer).status_code, 401)


if __name__ == "__main__":
    unittest.main()
