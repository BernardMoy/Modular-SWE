from fastapi import APIRouter, Depends

from app.models.line_status import LineStatusSummary
from app.services.line_status_service import LineStatusService, get_line_status_service

router = APIRouter()


@router.get("", response_model=list[LineStatusSummary])
async def get_line_statuses(
    line_status_service: LineStatusService = Depends(get_line_status_service),
) -> list[LineStatusSummary]:
    return await line_status_service.get_line_status_summaries()
