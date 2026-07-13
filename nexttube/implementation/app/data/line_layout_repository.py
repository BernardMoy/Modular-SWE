import json
from functools import lru_cache
from pathlib import Path

from app.models.line_layout import LayoutEdge, LayoutNode, LineLayout

_DEFAULT_DATA_DIR = Path(__file__).resolve().parents[3] / "data" / "live-tube-map-layouts"


class LineLayoutNotFoundError(Exception):
    pass


class LineLayoutRepository:
    def __init__(self, data_dir: Path = _DEFAULT_DATA_DIR):
        self._data_dir = data_dir

    def get_layout(self, line_id: str, direction: str) -> LineLayout:
        layout_path = self._data_dir / f"{line_id}.json"
        if not layout_path.exists():
            raise LineLayoutNotFoundError(line_id)

        raw = json.loads(layout_path.read_text())
        nodes_key = f"{direction}Nodes" if f"{direction}Nodes" in raw else "nodes"
        edges_key = f"{direction}Edges"

        return LineLayout(
            nodes=[
                LayoutNode(station_id=node["stationId"], x=node["x"], y=node["y"])
                for node in raw[nodes_key]
            ],
            edges=[
                LayoutEdge(from_station_id=edge["from"], to_station_id=edge["to"])
                for edge in raw[edges_key]
            ],
        )


@lru_cache
def get_line_layout_repository() -> LineLayoutRepository:
    return LineLayoutRepository()
