import { useEffect, useRef, useState } from "react";

export interface PollingState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
}

export function usePolling<T>(
  fetchFn: () => Promise<T>,
  intervalMs: number,
  deps: React.DependencyList,
  errorFallbackMessage: string,
): PollingState<T> {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const fetchFnRef = useRef(fetchFn);
  fetchFnRef.current = fetchFn;

  useEffect(() => {
    let cancelled = false;
    setLoading(true);

    function load() {
      fetchFnRef
        .current()
        .then((result) => {
          if (!cancelled) {
            setData(result);
            setError(null);
          }
        })
        .catch((err: unknown) => {
          if (!cancelled) {
            setError(err instanceof Error ? err.message : errorFallbackMessage);
          }
        })
        .finally(() => {
          if (!cancelled) setLoading(false);
        });
    }

    load();
    const intervalId = setInterval(load, intervalMs);
    return () => {
      cancelled = true;
      clearInterval(intervalId);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  return { data, loading, error };
}
