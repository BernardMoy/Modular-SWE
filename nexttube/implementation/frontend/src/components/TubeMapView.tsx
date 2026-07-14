import type { MapEdge, MapNode, TrainMarker } from "../types";

const GRID_SPACING = 60;
const PADDING = 50;
const NODE_RADIUS = 6;
const TRAIN_RADIUS = 8;

const DISRUPTION_COLORS: Record<string, string> = {
  Suspended: "#dc2626",
  "Severe Delays": "#f97316",
  "Minor Delays": "#eab308",
  "Planned Closure": "#6b7280",
  "Part Closure": "#6b7280",
};

const DELAY_COLOR = "#334155";
const DELAY_ALERT_COLOR = "#dc2626";
const DELAY_ALERT_THRESHOLD_MINUTES = 10;

function edgeColor(category: string | null, lineColor: string): string {
  return (category && DISRUPTION_COLORS[category]) || lineColor;
}

function delayLabel(delayMinutes: number): string {
  return `+${delayMinutes}`;
}

function delayColor(delayMinutes: number): string {
  return delayMinutes > DELAY_ALERT_THRESHOLD_MINUTES ? DELAY_ALERT_COLOR : DELAY_COLOR;
}

export default function TubeMapView({
  nodes,
  edges,
  trains,
  lineColor,
}: {
  nodes: MapNode[];
  edges: MapEdge[];
  trains: TrainMarker[];
  lineColor: string;
}) {
  if (nodes.length === 0) {
    return <p className="text-slate-400">No map data available.</p>;
  }

  const minX = Math.min(...nodes.map((n) => n.x));
  const maxX = Math.max(...nodes.map((n) => n.x));
  const minY = Math.min(...nodes.map((n) => n.y));
  const maxY = Math.max(...nodes.map((n) => n.y));

  const width = (maxX - minX) * GRID_SPACING + PADDING * 2;
  const height = (maxY - minY) * GRID_SPACING + PADDING * 2;

  const positionById = new Map<string, { x: number; y: number }>();
  for (const node of nodes) {
    positionById.set(node.station_id, {
      x: (node.x - minX) * GRID_SPACING + PADDING,
      y: (node.y - minY) * GRID_SPACING + PADDING,
    });
  }

  function markerPosition(train: TrainMarker): { x: number; y: number } | null {
    if (train.at_station_id) {
      return positionById.get(train.at_station_id) ?? null;
    }
    if (train.between_station_ids) {
      const [aId, bId] = train.between_station_ids;
      const a = positionById.get(aId);
      const b = positionById.get(bId);
      if (!a || !b) return null;
      return { x: (a.x + b.x) / 2, y: (a.y + b.y) / 2 };
    }
    return null;
  }

  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      className="h-auto w-full"
      role="img"
      aria-label="Live tube map"
    >
      {edges.map((edge) => {
        const from = positionById.get(edge.from_station_id);
        const to = positionById.get(edge.to_station_id);
        if (!from || !to) return null;
        const midX = (from.x + to.x) / 2;
        const midY = (from.y + to.y) / 2;
        return (
          <g key={`${edge.from_station_id}-${edge.to_station_id}`}>
            <line
              x1={from.x}
              y1={from.y}
              x2={to.x}
              y2={to.y}
              stroke={edgeColor(edge.disruption_category, lineColor)}
              strokeWidth={4}
              strokeLinecap="round"
            />
            {edge.delay_minutes != null && (
              <text
                x={midX}
                y={midY - 6}
                fontSize={10}
                fontWeight="bold"
                textAnchor="middle"
                fill={delayColor(edge.delay_minutes)}
              >
                {delayLabel(edge.delay_minutes)}
              </text>
            )}
          </g>
        );
      })}

      {nodes.map((node) => {
        const pos = positionById.get(node.station_id)!;
        return (
          <g key={node.station_id}>
            <circle cx={pos.x} cy={pos.y} r={NODE_RADIUS} fill="white" stroke={lineColor} strokeWidth={2} />
            <text x={pos.x + 10} y={pos.y + 4} fontSize={10} fill="#334155">
              {node.name}
            </text>
            {node.delay_minutes != null && (
              <text
                x={pos.x + 10}
                y={pos.y + 16}
                fontSize={10}
                fontWeight="bold"
                fill={delayColor(node.delay_minutes)}
              >
                {delayLabel(node.delay_minutes)}
              </text>
            )}
          </g>
        );
      })}

      {trains.map((train) => {
        const pos = markerPosition(train);
        if (!pos) return null;
        return (
          <circle
            key={train.vehicle_id}
            cx={pos.x}
            cy={pos.y}
            r={TRAIN_RADIUS}
            fill="#0f172a"
            stroke="white"
            strokeWidth={2}
          />
        );
      })}
    </svg>
  );
}
