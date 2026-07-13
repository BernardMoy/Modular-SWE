from pydantic import BaseModel


class LayoutNode(BaseModel):
    station_id: str
    x: float
    y: float


class LayoutEdge(BaseModel):
    from_station_id: str
    to_station_id: str


class LineLayout(BaseModel):
    nodes: list[LayoutNode]
    edges: list[LayoutEdge]

    def next_station_id(self, from_station_id: str) -> str | None:
        for edge in self.edges:
            if edge.from_station_id == from_station_id:
                return edge.to_station_id
        return None

    def edge_pairs(self) -> dict[frozenset[str], LayoutEdge]:
        return {
            frozenset((edge.from_station_id, edge.to_station_id)): edge for edge in self.edges
        }
