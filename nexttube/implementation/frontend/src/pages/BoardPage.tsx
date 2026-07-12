import { useEffect, useState } from "react";
import { Navigate, useLocation, useNavigate } from "react-router-dom";
import { ApiError, getArrivalBoards } from "../api/client";
import ArrivalBoardCard from "../components/ArrivalBoardCard";
import type { ArrivalBoard, Line, Station } from "../types";

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

  const [boards, setBoards] = useState<ArrivalBoard[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!station || !line) return;

    let cancelled = false;

    function load() {
      getArrivalBoards(station!.id, line!.id)
        .then((result) => {
          if (!cancelled) {
            setBoards(result);
            setError(null);
          }
        })
        .catch((err: unknown) => {
          if (!cancelled) {
            setError(err instanceof ApiError ? err.message : "Couldn't load arrivals.");
          }
        })
        .finally(() => {
          if (!cancelled) setLoading(false);
        });
    }

    load();
    const intervalId = setInterval(load, REFRESH_INTERVAL_MS);
    return () => {
      cancelled = true;
      clearInterval(intervalId);
    };
  }, [station, line]);

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

      {loading && <p className="text-slate-400">Loading arrivals…</p>}
      {error && <p className="text-red-600">{error}</p>}

      {!loading && !error && boards.length === 0 && (
        <p className="text-slate-400">No arrivals right now.</p>
      )}

      <div className="flex flex-col gap-4">
        {boards.map((board) => (
          <ArrivalBoardCard key={board.direction} board={board} />
        ))}
      </div>
    </main>
  );
}
