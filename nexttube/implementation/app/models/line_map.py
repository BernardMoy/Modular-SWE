from pydantic import BaseModel


class MapNode(BaseModel):
    station_id: str
    name: str
    x: float
    y: float
    delay_minutes: int | None = None


class MapEdge(BaseModel):
    from_station_id: str
    to_station_id: str
    disruption_category: str | None = None
    delay_minutes: int | None = None


class TrainMarker(BaseModel):
    vehicle_id: str
    at_station_id: str | None = None
    between_station_ids: list[str] | None = None


class LineMapView(BaseModel):
    line_id: str
    direction: str
    nodes: list[MapNode]
    edges: list[MapEdge]
    trains: list[TrainMarker]
