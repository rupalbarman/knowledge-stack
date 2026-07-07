from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ProjectOut(BaseModel):
    id: UUID
    name: str
    created_at: datetime


class UserOut(BaseModel):
    id: UUID
    email: str
    created_at: datetime
    project: ProjectOut | None


class FolderCreateRequest(BaseModel):
    name: str
    parent_id: UUID | None = None


class FolderOut(BaseModel):
    id: UUID
    project_id: UUID
    parent_id: UUID | None
    name: str
    created_at: datetime


class FileOut(BaseModel):
    id: UUID
    project_id: UUID
    folder_id: UUID | None
    name: str
    content_type: str | None
    size_bytes: int
    storage_key: str
    created_at: datetime


class TaskOut(BaseModel):
    id: UUID
    project_id: UUID
    file_id: UUID
    type: str
    status: str
    error: str | None
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
