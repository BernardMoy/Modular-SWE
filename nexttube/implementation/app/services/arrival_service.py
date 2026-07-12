from dataclasses import dataclass
from functools import lru_cache

from app.clients.tfl_client import RawArrival, TflClient, get_tfl_client
from app.data.station_repository import StationRepository, get_station_repository
from app.models.arrival import ArrivalBoard, ArrivalBoardEntry, format_time_display
from app.services import platform_info

_DIRECTION_ORDER = ["Northbound", "Eastbound", "Southbound", "Westbound"]


class StationNotFoundError(Exception):
    pass


class LineNotServedError(Exception):
    pass


@dataclass
class _MergedEntry:
    destination_name: str
    time_to_station: int
    platform: str


class ArrivalService:
    def __init__(self, tfl_client: TflClient, station_repository: StationRepository):
        self._tfl_client = tfl_client
        self._station_repository = station_repository

    async def get_arrival_boards(self, station_id: str, line_id: str) -> list[ArrivalBoard]:
        station = self._station_repository.get_station(station_id)
        if station is None:
            raise StationNotFoundError(station_id)
        if not any(line.id == line_id for line in station.lines):
            raise LineNotServedError(f"Line '{line_id}' is not served by station '{station_id}'")

        raw_arrivals = await self._tfl_client.get_arrivals(line_id)
        # naptanId on an arrival identifies the specific platform stop point, which
        # extends the station's own id (e.g. "940GZZLUACT2"), so match by prefix.
        station_arrivals = [a for a in raw_arrivals if a.naptan_id.startswith(station_id)]

        entries_by_direction = self._group_and_merge(station_arrivals)

        boards = []
        for direction in _DIRECTION_ORDER:
            merged_entries = entries_by_direction.get(direction)
            if not merged_entries:
                continue
            merged_entries.sort(key=lambda e: e.time_to_station)
            boards.append(
                ArrivalBoard(
                    direction=direction,
                    entries=[
                        ArrivalBoardEntry(
                            index=index,
                            destination_name=entry.destination_name,
                            time_display=format_time_display(entry.time_to_station),
                            platform=entry.platform,
                        )
                        for index, entry in enumerate(merged_entries, start=1)
                    ],
                )
            )
        return boards

    @staticmethod
    def _group_and_merge(arrivals: list[RawArrival]) -> dict[str, list[_MergedEntry]]:
        groups: dict[tuple[str, str], list[RawArrival]] = {}
        platform_numbers_by_key: dict[tuple[str, str], set[str]] = {}

        for arrival in arrivals:
            info = platform_info.parse(arrival.platform_name)
            if info.direction is None:
                continue
            key = (info.direction, arrival.vehicle_id)
            groups.setdefault(key, []).append(arrival)
            if info.platform_number is not None:
                platform_numbers_by_key.setdefault(key, set()).add(info.platform_number)

        entries_by_direction: dict[str, list[_MergedEntry]] = {}
        for (direction, _vehicle_id), members in groups.items():
            soonest = min(members, key=lambda a: a.time_to_station)
            platform_numbers = sorted(
                platform_numbers_by_key.get((direction, _vehicle_id), set()), key=int
            )
            entries_by_direction.setdefault(direction, []).append(
                _MergedEntry(
                    destination_name=soonest.destination_name,
                    time_to_station=soonest.time_to_station,
                    platform=",".join(platform_numbers) if platform_numbers else "-",
                )
            )
        return entries_by_direction


@lru_cache
def get_arrival_service() -> ArrivalService:
    return ArrivalService(get_tfl_client(), get_station_repository())
