from functools import lru_cache

from app.clients.delay_estimates_client import RawDelayEstimate
from app.models.line_layout import LineLayout
from app.models.line_map import MapEdge, MapNode
from app.services.train_position_resolver import TrainPositionResolver, get_train_position_resolver


class DelayEstimateResolver:
    def __init__(self, train_position_resolver: TrainPositionResolver):
        self._train_position_resolver = train_position_resolver

    def resolve(
        self,
        estimates: list[RawDelayEstimate],
        trackernet_code: str,
        layout: LineLayout,
        nodes: list[MapNode],
        edges: list[MapEdge],
    ) -> tuple[list[MapNode], list[MapEdge]]:
        seconds_by_station, seconds_by_edge_pair = self._group_seconds(
            estimates, trackernet_code, layout
        )

        new_nodes = [
            node.model_copy(
                update={"delay_minutes": self._average_minutes(seconds_by_station[node.station_id])}
            )
            if node.station_id in seconds_by_station
            else node
            for node in nodes
        ]
        new_edges = [
            self._with_delay(edge, seconds_by_edge_pair) for edge in edges
        ]
        return new_nodes, new_edges

    def _group_seconds(
        self,
        estimates: list[RawDelayEstimate],
        trackernet_code: str,
        layout: LineLayout,
    ) -> tuple[dict[str, list[float]], dict[frozenset[str], list[float]]]:
        edge_pairs = layout.edge_pairs()
        seconds_by_station: dict[str, list[float]] = {}
        seconds_by_edge_pair: dict[frozenset[str], list[float]] = {}

        for estimate in estimates:
            if estimate.trackernet_code != trackernet_code:
                continue
            marker = self._train_position_resolver.resolve(
                estimate.vehicle_id,
                estimate.current_location,
                estimate.closest_station_id_to_arrival,
                layout,
            )
            if marker is None:
                continue
            if marker.at_station_id is not None:
                seconds_by_station.setdefault(marker.at_station_id, []).append(
                    estimate.delayed_seconds
                )
            elif marker.between_station_ids is not None:
                pair = frozenset(marker.between_station_ids)
                if pair in edge_pairs:
                    seconds_by_edge_pair.setdefault(pair, []).append(estimate.delayed_seconds)

        return seconds_by_station, seconds_by_edge_pair

    def _with_delay(
        self, edge: MapEdge, seconds_by_edge_pair: dict[frozenset[str], list[float]]
    ) -> MapEdge:
        pair = frozenset((edge.from_station_id, edge.to_station_id))
        if pair not in seconds_by_edge_pair:
            return edge
        return edge.model_copy(
            update={"delay_minutes": self._average_minutes(seconds_by_edge_pair[pair])}
        )

    @staticmethod
    def _average_minutes(seconds: list[float]) -> int:
        average_seconds = sum(seconds) / len(seconds)
        return max(round(average_seconds / 60), 0)


@lru_cache
def get_delay_estimate_resolver() -> DelayEstimateResolver:
    return DelayEstimateResolver(get_train_position_resolver())
