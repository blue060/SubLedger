from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class ServerBase(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    host: str = Field(min_length=1, max_length=255)
    provider: Optional[str] = Field(default=None, max_length=100)
    region: Optional[str] = Field(default=None, max_length=100)
    operating_system: Optional[str] = Field(default=None, max_length=100)
    ssh_port: int = Field(default=22, ge=1, le=65535)
    username: Optional[str] = Field(default=None, max_length=100)
    notes: Optional[str] = None
    is_active: bool = True

    @field_validator("name", "host")
    @classmethod
    def strip_required(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("不能为空")
        return value


class ServerCreate(ServerBase):
    pass


class ServerUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    host: Optional[str] = Field(default=None, min_length=1, max_length=255)
    provider: Optional[str] = Field(default=None, max_length=100)
    region: Optional[str] = Field(default=None, max_length=100)
    operating_system: Optional[str] = Field(default=None, max_length=100)
    ssh_port: Optional[int] = Field(default=None, ge=1, le=65535)
    username: Optional[str] = Field(default=None, max_length=100)
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class ServerOut(ServerBase):
    id: int
    service_count: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class DeployedServiceBase(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    domain: str = Field(min_length=1, max_length=255)
    server_id: int
    protocol: str = "https"
    internal_host: str = Field(default="127.0.0.1", min_length=1, max_length=255)
    internal_port: int = Field(ge=1, le=65535)
    container_name: Optional[str] = Field(default=None, max_length=100)
    notes: Optional[str] = None
    is_active: bool = True

    @field_validator("name", "domain", "internal_host")
    @classmethod
    def strip_service_fields(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("不能为空")
        return value

    @field_validator("domain")
    @classmethod
    def normalize_domain(cls, value: str) -> str:
        value = value.removeprefix("https://").removeprefix("http://").rstrip("/")
        if not value or " " in value:
            raise ValueError("请输入有效域名")
        return value

    @field_validator("protocol")
    @classmethod
    def validate_protocol(cls, value: str) -> str:
        value = value.lower()
        if value not in {"http", "https", "tcp", "udp"}:
            raise ValueError("协议仅支持 http、https、tcp 或 udp")
        return value


class DeployedServiceCreate(DeployedServiceBase):
    pass


class DeployedServiceUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    domain: Optional[str] = Field(default=None, min_length=1, max_length=255)
    server_id: Optional[int] = None
    protocol: Optional[str] = None
    internal_host: Optional[str] = Field(default=None, min_length=1, max_length=255)
    internal_port: Optional[int] = Field(default=None, ge=1, le=65535)
    container_name: Optional[str] = Field(default=None, max_length=100)
    notes: Optional[str] = None
    is_active: Optional[bool] = None

    @field_validator("domain")
    @classmethod
    def normalize_domain(cls, value: str | None) -> str | None:
        if value is None:
            return value
        value = value.strip().removeprefix("https://").removeprefix("http://").rstrip("/")
        if not value or " " in value:
            raise ValueError("请输入有效域名")
        return value

    @field_validator("protocol")
    @classmethod
    def validate_protocol(cls, value: str | None) -> str | None:
        if value is None:
            return value
        value = value.lower()
        if value not in {"http", "https", "tcp", "udp"}:
            raise ValueError("协议仅支持 http、https、tcp 或 udp")
        return value


class DeployedServiceOut(DeployedServiceBase):
    id: int
    server_name: str = ""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class InfrastructureOverview(BaseModel):
    servers: list[ServerOut]
    services: list[DeployedServiceOut]
