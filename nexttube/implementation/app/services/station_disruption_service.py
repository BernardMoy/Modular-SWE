from functools import lru_cache

from app.clients.tfl_client import TflClient, get_tfl_client
from app.data.station_repository import StationRepository, get_station_repository
from app.models.station_disruption import StationDisruption


class StationNotFoundError(Exception):
    pass


class StationDisruptionService:
    def __init__(self, tfl_client: TflClient, station_repository: StationRepository):
        self._tfl_client = tfl_client
        self._station_repository = station_repository

    async def get_station_disruptions(self, station_id: str) -> list[StationDisruption]:
        station = self._station_repository.get_station(station_id)
        if station is None:
            raise StationNotFoundError(station_id)

        raw_disruptions = await self._tfl_client.get_stop_point_disruptions()
        return [
            StationDisruption(type=raw.disruption_type, description=raw.description)
            for raw in raw_disruptions
            if raw.station_atco_code == station_id
        ]


@lru_cache
def get_station_disruption_service() -> StationDisruptionService:
    return StationDisruptionService(get_tfl_client(), get_station_repository())
