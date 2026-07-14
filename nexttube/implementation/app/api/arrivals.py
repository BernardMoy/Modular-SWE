from fastapi import APIRouter, Depends, HTTPException, Query

from app.models.arrival import ArrivalBoard
from app.services.arrival_service import (
    ArrivalService,
    LineNotServedError,
    StationNotFoundError,
    get_arrival_service,
)

router = APIRouter()


@router.get("", response_model=list[ArrivalBoard])
async def get_arrivals(
    station_id: str = Query(...),
    line_id: str = Query(...),
    arrival_service: ArrivalService = Depends(get_arrival_service),
) -> list[ArrivalBoard]:
    try:
        return await arrival_service.get_arrival_boards(station_id, line_id)
    except StationNotFoundError:
        raise HTTPException(status_code=404, detail=f"Unknown station '{station_id}'")
    except LineNotServedError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
