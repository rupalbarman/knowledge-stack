from fastapi import APIRouter, Depends

from app.db import get_pool
from app.dependencies import get_current_project
from app.models import AnalyticsSummary, DocumentStatusBreakdown
from app.repositories import analytics as analytics_repo
from app.repositories import folders as folders_repo

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/summary", response_model=AnalyticsSummary)
async def get_summary(project=Depends(get_current_project)) -> AnalyticsSummary:
    pool = get_pool()
    async with pool.acquire() as conn:
        summary = await analytics_repo.get_summary(conn, project["id"])
        total_folders = await folders_repo.count_by_project_id(conn, project["id"])

    return AnalyticsSummary(
        total_documents=summary["total_documents"],
        total_folders=total_folders,
        storage_used_bytes=summary["storage_used_bytes"],
        total_chunks=summary["total_chunks"],
        documents_by_status=DocumentStatusBreakdown(
            pending=summary["pending_documents"],
            processing=summary["processing_documents"],
            completed=summary["completed_documents"],
            failed=summary["failed_documents"],
        ),
    )
