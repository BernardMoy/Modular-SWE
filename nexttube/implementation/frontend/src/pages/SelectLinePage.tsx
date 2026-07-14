import { Navigate, useLocation, useNavigate } from "react-router-dom";
import LineList from "../components/LineList";
import type { Line, Station } from "../types";

interface LocationState {
  station?: Station;
}

export default function SelectLinePage() {
  const { state } = useLocation() as { state: LocationState | null };
  const navigate = useNavigate();
  const station = state?.station;

  if (!station) {
    return <Navigate to="/" replace />;
  }

  function selectLine(line: Line) {
    navigate("/board", { state: { station, line } });
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-lg flex-col gap-6 px-4 py-12">
      <button
        onClick={() => navigate("/")}
        className="self-start text-sm text-slate-500 hover:text-slate-800"
      >
        ← Back to search
      </button>

      <div>
        <h1 className="text-2xl font-bold text-slate-900">{station.name}</h1>
        <p className="text-slate-500">Served by multiple lines — pick one</p>
      </div>

      <LineList lines={station.lines} onSelect={selectLine} />
    </main>
  );
}
