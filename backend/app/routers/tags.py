from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, get_current_user_id
from app.models import Tag
from app.schemas.tag import TagCreate, TagUpdate, TagOut

router = APIRouter(prefix="/api/tags", tags=["标签"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=list[TagOut])
def list_tags(db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    return db.query(Tag).filter(Tag.user_id == user_id).order_by(Tag.id).all()


@router.post("", response_model=TagOut, status_code=status.HTTP_201_CREATED)
def create_tag(body: TagCreate, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    existing = db.query(Tag).filter(Tag.user_id == user_id, Tag.name == body.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="标签已存在")
    tag = Tag(**body.model_dump(), user_id=user_id)
    db.add(tag)
    db.commit()
    db.refresh(tag)
    return tag


@router.put("/{tag_id}", response_model=TagOut)
def update_tag(tag_id: int, body: TagUpdate, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    tag = db.query(Tag).filter(Tag.id == tag_id, Tag.user_id == user_id).first()
    if not tag:
        raise HTTPException(status_code=404, detail="标签不存在")
    new_name = body.model_dump(exclude_unset=True).get("name")
    if new_name and db.query(Tag.id).filter(
        Tag.user_id == user_id, Tag.name == new_name, Tag.id != tag_id
    ).first():
        raise HTTPException(status_code=400, detail="标签已存在")
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(tag, key, value)
    db.commit()
    db.refresh(tag)
    return tag


@router.delete("/{tag_id}")
def delete_tag(tag_id: int, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    tag = db.query(Tag).filter(Tag.id == tag_id, Tag.user_id == user_id).first()
    if not tag:
        raise HTTPException(status_code=404, detail="标签不存在")
    db.delete(tag)
    db.commit()
    return {"detail": "标签已删除"}
