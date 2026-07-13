from fastapi import APIRouter, Depends, HTTPException, Query

from app.models.line_map import LineMapView
from app.services.line_map_service import LineMapService, LineNotFoundError, get_line_map_service

router = APIRouter()


@router.get("/{line_id}", response_model=LineMapView)
async def get_line_map(
    line_id: str,
    direction: str = Query(..., pattern="^(inbound|outbound)$"),
    line_map_service: LineMapService = Depends(get_line_map_service),
) -> LineMapView:
    try:
        return await line_map_service.get_line_map(line_id, direction)
    except LineNotFoundError:
        raise HTTPException(status_code=404, detail=f"Unknown line '{line_id}'")
