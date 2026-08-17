from app.security import hash_password, verify_password


def test_hash_password_does_not_store_plaintext():
    password = "jobflow-test-password"

    hashed = hash_password(password)

    assert hashed != password
    assert hashed.startswith("$argon2")


def test_verify_password_accepts_correct_password():
    password = "jobflow-test-password"
    hashed = hash_password(password)

    assert verify_password(password, hashed) is True


def test_verify_password_rejects_wrong_password():
    hashed = hash_password("jobflow-test-password")

    assert verify_password("wrong-password", hashed) is False

import jwt
import pytest

from app.security import (
    JWT_SECRET,
    create_access_token,
    decode_access_token,
)


def test_create_and_decode_access_token():
    token = create_access_token(42)

    assert decode_access_token(token) == 42


def test_decode_access_token_rejects_invalid_token():
    with pytest.raises(jwt.InvalidTokenError):
        decode_access_token("not-a-valid-token")


def test_decode_access_token_rejects_tampered_token():
    token = create_access_token(42)
    tampered = token[:-1] + ("a" if token[-1] != "a" else "b")

    with pytest.raises(jwt.InvalidTokenError):
        decode_access_token(tampered)


def test_access_token_contains_expected_subject():
    token = create_access_token(42)

    payload = jwt.decode(
        token,
        JWT_SECRET,
        algorithms=["HS256"],
    )

    assert payload["sub"] == "42"
