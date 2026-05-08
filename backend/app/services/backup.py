import os
import shutil
import logging
from datetime import datetime

from sqlalchemy.orm import Session

from app.models import BackupRecord, AppSettings
from app.config import get_settings

logger = logging.getLogger("subledger")


def perform_backup(db: Session) -> BackupRecord:
    settings = get_settings()
    source = settings.DATABASE_URL.replace("sqlite:///", "")
    backup_dir = os.path.join(os.path.dirname(source), "backups")
    os.makedirs(backup_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = os.path.join(backup_dir, f"subledger_{timestamp}.db")
    shutil.copy2(source, dest)
    file_size = os.path.getsize(dest)

    record = BackupRecord(file_path=dest, file_size=file_size)
    db.add(record)

    app_settings = db.query(AppSettings).filter(AppSettings.id == 1).first()
    max_copies = 5
    if app_settings:
        max_copies = getattr(app_settings, 'backup_max_copies', 5) or 5

    db.flush()
    all_records = db.query(BackupRecord).order_by(BackupRecord.created_at.desc()).all()
    for old in all_records[max_copies:]:
        if os.path.exists(old.file_path):
            os.remove(old.file_path)
        db.delete(old)

    db.commit()
    logger.info(f"数据库备份完成: {dest} ({file_size} bytes)")
    return record
