from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.dependencies import get_current_user
from app.models import DeployedService, Server
from app.schemas.infrastructure import (
    DeployedServiceCreate,
    DeployedServiceOut,
    DeployedServiceUpdate,
    InfrastructureOverview,
    ServerCreate,
    ServerOut,
    ServerUpdate,
)

router = APIRouter(prefix="/api/infrastructure", tags=["系统管理"], dependencies=[Depends(get_current_user)])


def _server_out(server: Server) -> ServerOut:
    out = ServerOut.model_validate(server)
    out.service_count = len(server.services)
    return out


def _service_out(service: DeployedService) -> DeployedServiceOut:
    out = DeployedServiceOut.model_validate(service)
    out.server_name = service.server.name
    return out


def _get_server(db: Session, server_id: int) -> Server:
    server = db.query(Server).filter(Server.id == server_id).first()
    if not server:
        raise HTTPException(status_code=404, detail="服务器不存在")
    return server


def _get_service(db: Session, service_id: int) -> DeployedService:
    service = db.query(DeployedService).filter(DeployedService.id == service_id).first()
    if not service:
        raise HTTPException(status_code=404, detail="部署服务不存在")
    return service


@router.get("/overview", response_model=InfrastructureOverview)
def get_overview(db: Session = Depends(get_db)):
    servers = (
        db.query(Server)
        .options(selectinload(Server.services))
        .order_by(Server.is_active.desc(), Server.name.asc())
        .all()
    )
    services = (
        db.query(DeployedService)
        .order_by(DeployedService.is_active.desc(), DeployedService.name.asc())
        .all()
    )
    return InfrastructureOverview(
        servers=[_server_out(server) for server in servers],
        services=[_service_out(service) for service in services],
    )


@router.post("/servers", response_model=ServerOut, status_code=status.HTTP_201_CREATED)
def create_server(body: ServerCreate, db: Session = Depends(get_db)):
    server = Server(**body.model_dump())
    db.add(server)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="服务器名称已存在")
    db.refresh(server)
    return _server_out(server)


@router.put("/servers/{server_id}", response_model=ServerOut)
def update_server(server_id: int, body: ServerUpdate, db: Session = Depends(get_db)):
    server = _get_server(db, server_id)
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(server, key, value)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="服务器名称已存在")
    db.refresh(server)
    return _server_out(server)


@router.delete("/servers/{server_id}")
def delete_server(server_id: int, db: Session = Depends(get_db)):
    server = _get_server(db, server_id)
    if db.query(DeployedService).filter(DeployedService.server_id == server_id).first():
        raise HTTPException(status_code=400, detail="该服务器仍有关联服务，请先移动或删除服务")
    db.delete(server)
    db.commit()
    return {"detail": "服务器已删除"}


@router.post("/services", response_model=DeployedServiceOut, status_code=status.HTTP_201_CREATED)
def create_service(body: DeployedServiceCreate, db: Session = Depends(get_db)):
    _get_server(db, body.server_id)
    service = DeployedService(**body.model_dump())
    db.add(service)
    db.commit()
    db.refresh(service)
    return _service_out(service)


@router.put("/services/{service_id}", response_model=DeployedServiceOut)
def update_service(service_id: int, body: DeployedServiceUpdate, db: Session = Depends(get_db)):
    service = _get_service(db, service_id)
    update_data = body.model_dump(exclude_unset=True)
    if "server_id" in update_data:
        _get_server(db, update_data["server_id"])
    for key, value in update_data.items():
        setattr(service, key, value)
    db.commit()
    db.refresh(service)
    return _service_out(service)


@router.delete("/services/{service_id}")
def delete_service(service_id: int, db: Session = Depends(get_db)):
    service = _get_service(db, service_id)
    db.delete(service)
    db.commit()
    return {"detail": "部署服务已删除"}
