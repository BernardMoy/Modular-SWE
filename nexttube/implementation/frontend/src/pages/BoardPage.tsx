import { useEffect, useState } from "react";
import { Navigate, useLocation, useNavigate } from "react-router-dom";
import { getArrivalBoards, getStationDisruptions } from "../api/client";
import ArrivalBoardCard from "../components/ArrivalBoardCard";
import StationDisruptionList from "../components/StationDisruptionList";
import { usePolling } from "../hooks/usePolling";
import type { ArrivalBoard, Line, Station, StationDisruption } from "../types";

const REFRESH_INTERVAL_MS = 20_000;

interface LocationState {
  station?: Station;
  line?: Line;
}

export default function BoardPage() {
  const { state } = useLocation() as { state: LocationState | null };
  const navigate = useNavigate();
  const station = state?.station;
  const line = state?.line;

  const [disruptions, setDisruptions] = useState<StationDisruption[]>([]);

  useEffect(() => {
    if (!station) return;
    getStationDisruptions(station.id)
      .then(setDisruptions)
      .catch(() => setDisruptions([]));
  }, [station]);

  const {
    data: boards,
    loading,
    error,
  } = usePolling<ArrivalBoard[]>(
    () => (station && line ? getArrivalBoards(station.id, line.id) : Promise.resolve([])),
    REFRESH_INTERVAL_MS,
    [station, line],
    "Couldn't load arrivals.",
  );

  if (!station || !line) {
    return <Navigate to="/" replace />;
  }

  const backTarget = station.lines.length > 1 ? "/select-line" : "/";
  const backState = station.lines.length > 1 ? { station } : undefined;

  return (
    <main className="mx-auto flex min-h-screen max-w-2xl flex-col gap-6 px-4 py-12">
      <button
        onClick={() => navigate(backTarget, { state: backState })}
        className="self-start text-sm text-slate-500 hover:text-slate-800"
      >
        ← Back
      </button>

      <div className="flex items-center gap-3">
        <span
          className="h-4 w-4 shrink-0 rounded-full"
          style={{ backgroundColor: line.color }}
        />
        <h1 className="text-2xl font-bold text-slate-900">
          {station.name} — {line.name}
        </h1>
      </div>

      {disruptions.length > 0 && <StationDisruptionList disruptions={disruptions} />}

      {loading && <p className="text-slate-400">Loading arrivals…</p>}
      {error && <p className="text-red-600">{error}</p>}

      {!loading && !error && (boards?.length ?? 0) === 0 && (
        <p className="text-slate-400">No arrivals right now.</p>
      )}

      <div className="flex flex-col gap-4">
        {(boards ?? []).map((board) => (
          <ArrivalBoardCard key={board.direction} board={board} />
        ))}
      </div>
    </main>
  );
}
