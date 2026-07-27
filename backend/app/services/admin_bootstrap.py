import os
from pathlib import Path
import secrets

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


def load_or_create_runtime_secret(
    configured_secret: str,
    environment: str,
    secret_file: str,
) -> str:
    """Return an explicit secret or persist an automatically generated one.

    Production secrets are stored alongside the database in the Docker data
    volume so container recreation does not invalidate every login session.
    """
    configured_secret = configured_secret.strip()
    if configured_secret:
        validate_runtime_secret(configured_secret, environment)
        return configured_secret

    if environment.lower() != "production":
        return secrets.token_urlsafe(48)

    path = Path(secret_file)
    try:
        existing_secret = path.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        existing_secret = ""
    except OSError as exc:
        raise InitialAdminConfigurationError(
            f"无法读取自动生成的系统密钥文件 {path}: {exc}"
        ) from exc

    if existing_secret:
        validate_runtime_secret(existing_secret, environment)
        return existing_secret

    generated_secret = secrets.token_urlsafe(48)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(generated_secret)
    except FileExistsError:
        # Another worker may have created it between our read and write.
        try:
            generated_secret = path.read_text(encoding="utf-8").strip()
        except OSError as exc:
            raise InitialAdminConfigurationError(
                f"无法读取自动生成的系统密钥文件 {path}: {exc}"
            ) from exc
    except OSError as exc:
        raise InitialAdminConfigurationError(
            f"无法写入自动生成的系统密钥文件 {path}: {exc}"
        ) from exc

    validate_runtime_secret(generated_secret, environment)
    return generated_secret


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

    db.add(User(username=username, password_hash=hash_password(password), is_admin=True))
    db.commit()
    return True
