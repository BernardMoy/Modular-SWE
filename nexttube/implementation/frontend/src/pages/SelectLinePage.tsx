import { Navigate, useLocation, useNavigate } from "react-router-dom";
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

      <ul className="flex flex-col gap-3">
        {station.lines.map((line) => (
          <li key={line.id}>
            <button
              onClick={() => selectLine(line)}
              className="flex w-full items-center gap-4 rounded-lg border border-slate-200 px-4 py-4 text-left shadow-sm hover:bg-slate-50"
            >
              <span
                className="h-4 w-4 shrink-0 rounded-full"
                style={{ backgroundColor: line.color }}
              />
              <span className="font-medium text-slate-900">{line.name}</span>
            </button>
          </li>
        ))}
      </ul>
    </main>
  );
}
