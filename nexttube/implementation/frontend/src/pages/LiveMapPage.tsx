import { useState } from "react";
import { Navigate, useLocation, useNavigate } from "react-router-dom";
import { getLineMap } from "../api/client";
import TubeMapView from "../components/TubeMapView";
import { usePolling } from "../hooks/usePolling";
import type { Direction, Line, LineMapView } from "../types";

const REFRESH_INTERVAL_MS = 10_000;

interface LocationState {
  line?: Line;
}

export default function LiveMapPage() {
  const { state } = useLocation() as { state: LocationState | null };
  const navigate = useNavigate();
  const line = state?.line;
  const [direction, setDirection] = useState<Direction>("inbound");

  const { data: mapView, loading, error } = usePolling<LineMapView | null>(
    () => (line ? getLineMap(line.id, direction) : Promise.resolve(null)),
    REFRESH_INTERVAL_MS,
    [line, direction],
    "Couldn't load the live map.",
  );

  if (!line) {
    return <Navigate to="/select-map-line" replace />;
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-4xl flex-col gap-6 px-4 py-12">
      <button
        onClick={() => navigate("/select-map-line")}
        className="self-start text-sm text-slate-500 hover:text-slate-800"
      >
        ← Back to lines
      </button>

      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <span className="h-4 w-4 shrink-0 rounded-full" style={{ backgroundColor: line.color }} />
          <h1 className="text-2xl font-bold text-slate-900">{line.name}</h1>
        </div>

        <div className="flex overflow-hidden rounded-lg border border-slate-300">
          {(["inbound", "outbound"] as Direction[]).map((option) => (
            <button
              key={option}
              onClick={() => setDirection(option)}
              className={
                "px-4 py-2 text-sm font-medium capitalize " +
                (direction === option
                  ? "bg-slate-900 text-white"
                  : "bg-white text-slate-700 hover:bg-slate-50")
              }
            >
              {option}
            </button>
          ))}
        </div>
      </div>

      {loading && !mapView && <p className="text-slate-400">Loading map…</p>}
      {error && <p className="text-red-600">{error}</p>}

      {mapView && (
        <div className="rounded-lg border border-slate-200 p-4 shadow-sm">
          <TubeMapView
            nodes={mapView.nodes}
            edges={mapView.edges}
            trains={mapView.trains}
            lineColor={line.color}
          />
        </div>
      )}
    </main>
  );
}
