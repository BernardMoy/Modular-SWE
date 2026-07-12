import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getLineStatuses, searchStations } from "../api/client";
import LineStatusCard from "../components/LineStatusCard";
import type { LineStatusSummary, Station } from "../types";

export default function HomePage() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<Station[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lineStatuses, setLineStatuses] = useState<LineStatusSummary[]>([]);
  const navigate = useNavigate();

  useEffect(() => {
    getLineStatuses()
      .then(setLineStatuses)
      .catch(() => setLineStatuses([]));
  }, []);

  useEffect(() => {
    const trimmed = query.trim();
    if (trimmed.length === 0) {
      setResults([]);
      setError(null);
      return;
    }

    setLoading(true);
    setError(null);
    const timeoutId = setTimeout(() => {
      searchStations(trimmed)
        .then(setResults)
        .catch(() => setError("Couldn't search stations. Try again."))
        .finally(() => setLoading(false));
    }, 250);

    return () => clearTimeout(timeoutId);
  }, [query]);

  function selectStation(station: Station) {
    if (station.lines.length > 1) {
      navigate("/select-line", { state: { station } });
    } else {
      navigate("/board", { state: { station, line: station.lines[0] } });
    }
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-lg flex-col items-center gap-6 px-4 py-12">
      <h1 className="text-3xl font-bold text-slate-900">NextTube</h1>
      <p className="text-slate-500">Search for a station by name or 3-letter code</p>

      <input
        autoFocus
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="e.g. Baker Street or BST"
        className="w-full rounded-lg border border-slate-300 px-4 py-3 text-lg shadow-sm focus:border-slate-500 focus:outline-none"
      />

      {loading && <p className="text-slate-400">Searching…</p>}
      {error && <p className="text-red-600">{error}</p>}

      {results.length > 0 && (
        <ul className="w-full divide-y divide-slate-200 overflow-hidden rounded-lg border border-slate-200 shadow-sm">
          {results.map((station) => (
            <li key={station.id}>
              <button
                onClick={() => selectStation(station)}
                className="flex w-full items-center justify-between gap-4 px-4 py-3 text-left hover:bg-slate-50"
              >
                <span className="font-medium text-slate-900">{station.name}</span>
                <span className="rounded bg-slate-100 px-2 py-1 font-mono text-sm text-slate-600">
                  {station.code}
                </span>
              </button>
            </li>
          ))}
        </ul>
      )}

      {!loading && !error && query.trim().length > 0 && results.length === 0 && (
        <p className="text-slate-400">No stations found</p>
      )}

      {lineStatuses.length > 0 && (
        <div className="flex w-full flex-col gap-4">
          <h2 className="text-xl font-bold text-slate-900">Line status</h2>
          {lineStatuses.map((status) => (
            <LineStatusCard key={status.line_id} status={status} />
          ))}
        </div>
      )}
    </main>
  );
}
