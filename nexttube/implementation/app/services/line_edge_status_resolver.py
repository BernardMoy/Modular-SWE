from functools import lru_cache

from app.clients.tfl_client import RawLineStatus
from app.data.station_repository import StationRepository, get_station_repository
from app.models.line_layout import LineLayout
from app.models.line_map import MapEdge

_KNOWN_CATEGORIES = {
    "Suspended",
    "Severe Delays",
    "Minor Delays",
    "Planned Closure",
    "Part Closure",
}


class LineEdgeStatusResolver:
    def __init__(self, station_repository: StationRepository):
        self._station_repository = station_repository

    def resolve_edges(self, layout: LineLayout, statuses: list[RawLineStatus]) -> list[MapEdge]:
        disruptions_by_pair = self._disruptions_by_station_pair(statuses)

        edges = []
        for pair, edge in layout.edge_pairs().items():
            category = self._most_severe_category(disruptions_by_pair.get(pair, []))
            edges.append(
                MapEdge(
                    from_station_id=edge.from_station_id,
                    to_station_id=edge.to_station_id,
                    disruption_category=category,
                )
            )
        return edges

    def _disruptions_by_station_pair(
        self, statuses: list[RawLineStatus]
    ) -> dict[frozenset[str], list[RawLineStatus]]:
        by_pair: dict[frozenset[str], list[RawLineStatus]] = {}
        for status in statuses:
            if status.status_severity_description not in _KNOWN_CATEGORIES:
                continue
            for route in status.affected_routes:
                origin = self._station_repository.find_by_name(route.origin_name)
                destination = self._station_repository.find_by_name(route.destination_name)
                if origin is None or destination is None:
                    continue
                pair = frozenset((origin.id, destination.id))
                by_pair.setdefault(pair, []).append(status)
        return by_pair

    @staticmethod
    def _most_severe_category(statuses: list[RawLineStatus]) -> str | None:
        if not statuses:
            return None
        most_severe = min(statuses, key=lambda status: status.status_severity)
        return most_severe.status_severity_description


@lru_cache
def get_line_edge_status_resolver() -> LineEdgeStatusResolver:
    return LineEdgeStatusResolver(get_station_repository())
