from functools import lru_cache

from app.data.station_repository import StationRepository, get_station_repository
from app.models.line_layout import LineLayout
from app.models.line_map import TrainMarker
from app.services import train_location_parser


class TrainPositionResolver:
    def __init__(self, station_repository: StationRepository):
        self._station_repository = station_repository

    def resolve(
        self,
        vehicle_id: str,
        raw_location: str,
        naptan_id: str,
        layout: LineLayout,
    ) -> TrainMarker | None:
        parsed = train_location_parser.parse(raw_location)
        node_ids = {node.station_id for node in layout.nodes}

        if parsed.kind == "at_platform":
            station_id = self._resolve_by_naptan(naptan_id, node_ids)
            if station_id is None:
                return None
            return TrainMarker(vehicle_id=vehicle_id, at_station_id=station_id)

        if parsed.kind == "at_station":
            station_id = self._resolve_by_name(parsed.station_name, node_ids)
            if station_id is None:
                return None
            return TrainMarker(vehicle_id=vehicle_id, at_station_id=station_id)

        if parsed.kind == "left_station":
            station_id = self._resolve_by_name(parsed.station_name, node_ids)
            if station_id is None:
                return None
            next_station_id = layout.next_station_id(station_id)
            if next_station_id is None:
                return None
            return TrainMarker(
                vehicle_id=vehicle_id, between_station_ids=[station_id, next_station_id]
            )

        if parsed.kind == "between_stations":
            first_id = self._resolve_by_name(parsed.station_name, node_ids)
            second_id = self._resolve_by_name(parsed.second_station_name, node_ids)
            if first_id is None or second_id is None:
                return None
            return TrainMarker(vehicle_id=vehicle_id, between_station_ids=[first_id, second_id])

        return None

    def _resolve_by_name(self, name: str | None, node_ids: set[str]) -> str | None:
        if name is None:
            return None
        station = self._station_repository.find_by_name(name)
        if station is None or station.id not in node_ids:
            return None
        return station.id

    @staticmethod
    def _resolve_by_naptan(naptan_id: str, node_ids: set[str]) -> str | None:
        return next((node_id for node_id in node_ids if naptan_id.startswith(node_id)), None)


@lru_cache
def get_train_position_resolver() -> TrainPositionResolver:
    return TrainPositionResolver(get_station_repository())
