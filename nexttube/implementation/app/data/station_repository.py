import json
from functools import lru_cache
from pathlib import Path

from app.models.station import Line, Station, derive_code

_DEFAULT_DATA_DIR = Path(__file__).resolve().parents[3] / "data"


class StationRepository:
    def __init__(self, data_dir: Path = _DEFAULT_DATA_DIR):
        lines_by_id = self._load_lines(data_dir / "tube-lines.json")
        self._stations = self._load_stations(data_dir / "tube-stations.json", lines_by_id)

    @staticmethod
    def _load_lines(lines_path: Path) -> dict[str, Line]:
        records = json.loads(lines_path.read_text())
        return {record["id"]: Line(**record) for record in records}

    @staticmethod
    def _load_stations(stations_path: Path, lines_by_id: dict[str, Line]) -> dict[str, Station]:
        records = json.loads(stations_path.read_text())
        stations: dict[str, Station] = {}
        for record in records:
            station_id = record["id"]
            stations[station_id] = Station(
                id=station_id,
                name=record["name"],
                code=derive_code(station_id, record["name"]),
                lines=[lines_by_id[line_id] for line_id in record["lines"]],
            )
        return stations

    def search_stations(self, query: str) -> list[Station]:
        query_lower = query.lower()
        query_upper = query.upper()
        return [
            station
            for station in self._stations.values()
            if query_lower in station.name.lower() or station.code == query_upper
        ]

    def get_station(self, station_id: str) -> Station | None:
        return self._stations.get(station_id)


@lru_cache
def get_station_repository() -> StationRepository:
    return StationRepository()
