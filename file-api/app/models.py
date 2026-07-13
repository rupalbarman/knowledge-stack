from datetime import datetime
from typing import Literal
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


class FolderBreadcrumbItem(BaseModel):
    id: UUID
    name: str


class FolderTreeNode(BaseModel):
    id: UUID
    name: str
    children: list["FolderTreeNode"] = []


# needed for recursive pydantic model
FolderTreeNode.model_rebuild()


class FileOut(BaseModel):
    id: UUID
    project_id: UUID
    folder_id: UUID | None
    name: str
    content_type: str | None
    size_bytes: int
    storage_key: str
    created_at: datetime


class PresignedUrlOut(BaseModel):
    url: str
    expires_in: int


class SearchOptions(BaseModel):
    mode: Literal["dense", "sparse", "hybrid"] = "dense"
    top_k: int | None = None
    min_score: float | None = None


class SearchRequest(BaseModel):
    query: str
    folder_id: UUID | None = None
    options: SearchOptions | None = None


class SearchHit(BaseModel):
    file_id: UUID
    file_name: str
    chunk_index: int
    text: str
    score: float


class SearchResponse(BaseModel):
    hits: list[SearchHit]


class RerankerItem(BaseModel):
    score: float
    index: int


class TaskOut(BaseModel):
    id: UUID
    project_id: UUID
    file_ref: UUID
    file_name: str
    type: str
    reason: str
    status: str
    error: str | None
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
