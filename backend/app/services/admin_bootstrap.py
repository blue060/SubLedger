from sqlalchemy.orm import Session

from app.models import User
from app.security import hash_password

MIN_ADMIN_PASSWORD_LENGTH = 12
INSECURE_INITIAL_PASSWORDS = {
    "your-password",
    "your-secure-password",
    "replace-with-a-strong-password",
    "changeme",
    "change-me",
    "password",
}
INSECURE_SECRET_KEYS = {
    "subledger-default-secret-key-change-in-production-please",
    "change-me-in-production",
    "replace-with-a-random-secret-key",
}


class InitialAdminConfigurationError(RuntimeError):
    pass


def validate_runtime_secret(secret_key: str, environment: str) -> None:
    if environment.lower() != "production":
        return
    if len(secret_key) < 32 or secret_key.strip().lower() in INSECURE_SECRET_KEYS:
        raise InitialAdminConfigurationError(
            "公网生产环境必须设置至少32个字符的随机 SECRET_KEY，可使用 openssl rand -hex 32 生成"
        )


def ensure_initial_admin(db: Session, username: str, password: str) -> bool:
    """Create the first administrator from trusted server-side configuration.

    Existing installations are deliberately left untouched, even if the
    environment variable later changes or is removed.
    """
    if db.query(User.id).first() is not None:
        return False

    username = username.strip()
    if not username:
        raise InitialAdminConfigurationError("首次启动必须设置 ADMIN_USERNAME")
    if not password:
        raise InitialAdminConfigurationError(
            "首次启动必须通过环境变量 ADMIN_PASSWORD 设置管理员密码，网页初始化已禁用"
        )
    if len(password) < MIN_ADMIN_PASSWORD_LENGTH:
        raise InitialAdminConfigurationError(
            f"ADMIN_PASSWORD 至少需要 {MIN_ADMIN_PASSWORD_LENGTH} 个字符"
        )
    if password.strip().lower() in INSECURE_INITIAL_PASSWORDS:
        raise InitialAdminConfigurationError("ADMIN_PASSWORD 不能使用示例密码或常见弱密码")

    db.add(User(username=username, password_hash=hash_password(password)))
    db.commit()
    return True
