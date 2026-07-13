from fastapi import APIRouter, Depends

from app.data.station_repository import StationRepository, get_station_repository
from app.models.station import Line

router = APIRouter()


@router.get("", response_model=list[Line])
def list_lines(
    station_repository: StationRepository = Depends(get_station_repository),
) -> list[Line]:
    return station_repository.list_lines()
