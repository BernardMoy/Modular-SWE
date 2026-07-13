from fastapi import APIRouter, Depends, HTTPException

from app.models.station_disruption import StationDisruption
from app.services.station_disruption_service import (
    StationDisruptionService,
    StationNotFoundError,
    get_station_disruption_service,
)

router = APIRouter()


@router.get("/{station_id}", response_model=list[StationDisruption])
async def get_station_disruptions(
    station_id: str,
    station_disruption_service: StationDisruptionService = Depends(get_station_disruption_service),
) -> list[StationDisruption]:
    try:
        return await station_disruption_service.get_station_disruptions(station_id)
    except StationNotFoundError:
        raise HTTPException(status_code=404, detail=f"Unknown station '{station_id}'")
