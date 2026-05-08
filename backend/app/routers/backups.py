import os

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import BackupRecord
from app.schemas.backup import BackupOut
from app.services.backup import perform_backup

router = APIRouter(prefix="/api/backups", tags=["备份"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=list[BackupOut])
def list_backups(db: Session = Depends(get_db)):
    return db.query(BackupRecord).order_by(BackupRecord.created_at.desc()).all()


@router.post("/trigger", response_model=BackupOut)
def trigger_backup(db: Session = Depends(get_db)):
    record = perform_backup(db)
    return record


@router.get("/{backup_id}/download")
def download_backup(backup_id: int, db: Session = Depends(get_db)):
    record = db.query(BackupRecord).filter(BackupRecord.id == backup_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="备份不存在")
    if not os.path.exists(record.file_path):
        raise HTTPException(status_code=404, detail="备份文件不存在")
    return FileResponse(record.file_path, filename=os.path.basename(record.file_path))


@router.delete("/{backup_id}")
def delete_backup(backup_id: int, db: Session = Depends(get_db)):
    record = db.query(BackupRecord).filter(BackupRecord.id == backup_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="备份不存在")
    if os.path.exists(record.file_path):
        os.remove(record.file_path)
    db.delete(record)
    db.commit()
    return {"detail": "备份已删除"}
