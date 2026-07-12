import type { ArrivalBoard, LineStatusSummary, Station, StationDisruption } from "../types";

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
  ) {
    super(message);
  }
}

async function getJson<T>(url: string): Promise<T> {
  const response = await fetch(url);
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new ApiError(body?.detail ?? response.statusText, response.status);
  }
  return response.json() as Promise<T>;
}

export function searchStations(query: string): Promise<Station[]> {
  const params = new URLSearchParams({ q: query });
  return getJson<Station[]>(`/api/stations/search?${params}`);
}

export function getArrivalBoards(
  stationId: string,
  lineId: string,
): Promise<ArrivalBoard[]> {
  const params = new URLSearchParams({ station_id: stationId, line_id: lineId });
  return getJson<ArrivalBoard[]>(`/api/arrivals?${params}`);
}

export function getLineStatuses(): Promise<LineStatusSummary[]> {
  return getJson<LineStatusSummary[]>("/api/line-statuses");
}

export function getStationDisruptions(stationId: string): Promise<StationDisruption[]> {
  return getJson<StationDisruption[]>(`/api/station-disruptions/${stationId}`);
}
