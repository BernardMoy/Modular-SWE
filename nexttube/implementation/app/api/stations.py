from fastapi import APIRouter, Depends, Query

from app.data.station_repository import StationRepository, get_station_repository
from app.models.station import Station

router = APIRouter()


@router.get("/search", response_model=list[Station])
def search_stations(
    q: str = Query(..., min_length=1),
    station_repository: StationRepository = Depends(get_station_repository),
) -> list[Station]:
    return station_repository.search_stations(q)
