import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getLines } from "../api/client";
import LineList from "../components/LineList";
import type { Line } from "../types";

export default function SelectMapLinePage() {
  const navigate = useNavigate();
  const [lines, setLines] = useState<Line[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getLines()
      .then(setLines)
      .catch(() => setError("Couldn't load lines. Try again."));
  }, []);

  function selectLine(line: Line) {
    navigate("/live-map", { state: { line } });
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
        <h1 className="text-2xl font-bold text-slate-900">Live train map</h1>
        <p className="text-slate-500">Pick a line to view</p>
      </div>

      {error && <p className="text-red-600">{error}</p>}

      <LineList lines={lines} onSelect={selectLine} />
    </main>
  );
}
