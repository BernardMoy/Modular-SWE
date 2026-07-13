from functools import lru_cache

from app.clients.delay_estimates_client import DelayEstimatesClient, get_delay_estimates_client
from app.clients.tfl_client import RawArrival, TflClient, get_tfl_client
from app.data.line_layout_repository import LineLayoutRepository, get_line_layout_repository
from app.data.station_repository import StationRepository, get_station_repository
from app.data.trackernet_codes import get_trackernet_code
from app.models.line_map import LineMapView, MapNode
from app.services.delay_estimate_resolver import (
    DelayEstimateResolver,
    get_delay_estimate_resolver,
)
from app.services.line_edge_status_resolver import (
    LineEdgeStatusResolver,
    get_line_edge_status_resolver,
)
from app.services.train_position_resolver import TrainPositionResolver, get_train_position_resolver


class LineNotFoundError(Exception):
    pass


class LineMapService:
    def __init__(
        self,
        tfl_client: TflClient,
        station_repository: StationRepository,
        line_layout_repository: LineLayoutRepository,
        line_edge_status_resolver: LineEdgeStatusResolver,
        train_position_resolver: TrainPositionResolver,
        delay_estimates_client: DelayEstimatesClient,
        delay_estimate_resolver: DelayEstimateResolver,
    ):
        self._tfl_client = tfl_client
        self._station_repository = station_repository
        self._line_layout_repository = line_layout_repository
        self._line_edge_status_resolver = line_edge_status_resolver
        self._train_position_resolver = train_position_resolver
        self._delay_estimates_client = delay_estimates_client
        self._delay_estimate_resolver = delay_estimate_resolver

    async def get_line_map(self, line_id: str, direction: str) -> LineMapView:
        if line_id not in self._station_repository.list_line_ids():
            raise LineNotFoundError(line_id)

        layout = self._line_layout_repository.get_layout(line_id, direction)
        statuses = await self._tfl_client.get_line_statuses([line_id])
        arrivals = await self._tfl_client.get_arrivals(line_id)
        estimates = await self._delay_estimates_client.get_delay_estimates()

        nodes = [
            MapNode(
                station_id=node.station_id,
                name=self._station_name(node.station_id),
                x=node.x,
                y=node.y,
            )
            for node in layout.nodes
        ]
        edges = self._line_edge_status_resolver.resolve_edges(layout, statuses)
        nodes, edges = self._delay_estimate_resolver.resolve(
            estimates, get_trackernet_code(line_id), layout, nodes, edges
        )

        trains = []
        for arrival in self._soonest_arrival_per_train(arrivals, direction):
            marker = self._train_position_resolver.resolve(
                arrival.vehicle_id, arrival.current_location, arrival.naptan_id, layout
            )
            if marker is not None:
                trains.append(marker)

        return LineMapView(line_id=line_id, direction=direction, nodes=nodes, edges=edges, trains=trains)

    def _station_name(self, station_id: str) -> str:
        station = self._station_repository.get_station(station_id)
        return station.name if station is not None else station_id

    @staticmethod
    def _soonest_arrival_per_train(
        arrivals: list[RawArrival], direction: str
    ) -> list[RawArrival]:
        soonest_by_vehicle: dict[str, RawArrival] = {}
        for arrival in arrivals:
            if arrival.direction != direction:
                continue
            current = soonest_by_vehicle.get(arrival.vehicle_id)
            if current is None or arrival.time_to_station < current.time_to_station:
                soonest_by_vehicle[arrival.vehicle_id] = arrival
        return list(soonest_by_vehicle.values())


@lru_cache
def get_line_map_service() -> LineMapService:
    return LineMapService(
        get_tfl_client(),
        get_station_repository(),
        get_line_layout_repository(),
        get_line_edge_status_resolver(),
        get_train_position_resolver(),
        get_delay_estimates_client(),
        get_delay_estimate_resolver(),
    )
