
import pytest
import jwt

from backend import auth_service


TEST_JWT_SECRET = (
    "machinedoctor-unit-test-secret-at-least-32-bytes"
)


def test_password_hashing():
    password = "ExampleStrongPassword123!"

    hashed = auth_service.hash_password(password)

    assert hashed != password

    assert auth_service.verify_password(
        password,
        hashed,
    )

    assert not auth_service.verify_password(
        "WrongPassword",
        hashed,
    )


def test_access_token_round_trip(monkeypatch):
    monkeypatch.setattr(
        auth_service,
        "JWT_SECRET_KEY",
        TEST_JWT_SECRET,
    )

    token = auth_service.create_access_token(7)

    assert auth_service.decode_access_token(token) == 7


def test_invalid_token_rejected(monkeypatch):
    monkeypatch.setattr(
        auth_service,
        "JWT_SECRET_KEY",
        TEST_JWT_SECRET,
    )

    with pytest.raises(jwt.InvalidTokenError):
        auth_service.decode_access_token(
            "invalid.token.value"
        )


def test_missing_secret_rejected(monkeypatch):
    monkeypatch.setattr(
        auth_service,
        "JWT_SECRET_KEY",
        None,
    )

    with pytest.raises(RuntimeError):
        auth_service.create_access_token(1)


def test_short_secret_rejected(monkeypatch):
    monkeypatch.setattr(
        auth_service,
        "JWT_SECRET_KEY",
        "short-secret",
    )

    with pytest.raises(
        RuntimeError,
        match="32 bytes",
    ):
        auth_service.create_access_token(1)


def test_invalid_token_lifetime_rejected(monkeypatch):
    monkeypatch.setattr(
        auth_service,
        "JWT_SECRET_KEY",
        TEST_JWT_SECRET,
    )

    monkeypatch.setattr(
        auth_service,
        "ACCESS_TOKEN_EXPIRE_MINUTES",
        0,
    )

    with pytest.raises(
        RuntimeError,
        match="positive",
    ):
        auth_service.create_access_token(1)
