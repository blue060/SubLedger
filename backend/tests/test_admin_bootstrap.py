import pytest

from app.models import User
from app.security import verify_password
from app.services.admin_bootstrap import InitialAdminConfigurationError, ensure_initial_admin, validate_runtime_secret


def test_initial_admin_is_created_from_server_configuration(db):
    assert ensure_initial_admin(db, "admin", "a-secure-password-2026") is True

    user = db.query(User).one()
    assert user.username == "admin"
    assert verify_password("a-secure-password-2026", user.password_hash)


@pytest.mark.parametrize("password", ["", "short", "your-secure-password", "password"])
def test_initial_admin_rejects_missing_or_insecure_password(db, password):
    with pytest.raises(InitialAdminConfigurationError):
        ensure_initial_admin(db, "admin", password)
    assert db.query(User).count() == 0


def test_existing_admin_is_never_overwritten_from_environment(db):
    ensure_initial_admin(db, "admin", "original-password-2026")
    original_hash = db.query(User).one().password_hash

    assert ensure_initial_admin(db, "another-admin", "different-password-2026") is False
    user = db.query(User).one()
    assert user.username == "admin"
    assert user.password_hash == original_hash
    assert verify_password("original-password-2026", user.password_hash)


def test_production_rejects_default_or_short_secret_key():
    with pytest.raises(InitialAdminConfigurationError):
        validate_runtime_secret("subledger-default-secret-key-change-in-production-please", "production")
    with pytest.raises(InitialAdminConfigurationError):
        validate_runtime_secret("too-short", "production")


def test_random_production_secret_and_development_mode_are_allowed():
    validate_runtime_secret("b7c13477e2af9a64e5d4b6d6a974376a" * 2, "production")
    validate_runtime_secret("development-only", "development")
