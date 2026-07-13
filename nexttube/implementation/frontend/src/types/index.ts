export interface Line {
  id: string;
  name: string;
  color: string;
}

export interface Station {
  id: string;
  name: string;
  code: string;
  lines: Line[];
}

export interface ArrivalBoardEntry {
  index: number;
  destination_name: string;
  time_display: string;
  platform: string;
}

export interface ArrivalBoard {
  direction: string;
  entries: ArrivalBoardEntry[];
}

export interface RouteSection {
  start: string;
  end: string;
  bidirectional: boolean;
}

export interface LineSeverityGroup {
  severity_description: string;
  route_sections: RouteSection[];
  reasons: string[];
}

export interface LineStatusSummary {
  line_id: string;
  line_name: string;
  severities: LineSeverityGroup[];
}

export interface StationDisruption {
  type: string;
  description: string;
}

export type Direction = "inbound" | "outbound";

export interface MapNode {
  station_id: string;
  name: string;
  x: number;
  y: number;
}

export interface MapEdge {
  from_station_id: string;
  to_station_id: string;
  disruption_category: string | null;
}

export interface TrainMarker {
  vehicle_id: string;
  at_station_id: string | null;
  between_station_ids: string[] | null;
}

export interface LineMapView {
  line_id: string;
  direction: Direction;
  nodes: MapNode[];
  edges: MapEdge[];
  trains: TrainMarker[];
}
