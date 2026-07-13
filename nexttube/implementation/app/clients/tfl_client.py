import datetime
from functools import lru_cache

import httpx
from pydantic import BaseModel

_BASE_URL = "https://api.tfl.gov.uk"


class TflClientError(Exception):
    pass


class RawArrival(BaseModel):
    vehicle_id: str
    naptan_id: str
    platform_name: str
    destination_name: str
    time_to_station: int
    direction: str
    current_location: str


class RawRouteSection(BaseModel):
    origin_name: str
    destination_name: str


class RawLineStatus(BaseModel):
    line_id: str
    line_name: str
    status_severity: int
    status_severity_description: str
    reason: str | None
    affected_routes: list[RawRouteSection]


class RawStopPointDisruption(BaseModel):
    station_atco_code: str
    disruption_type: str
    description: str


class TflClient:
    def __init__(self, client: httpx.AsyncClient | None = None):
        self._client = client or httpx.AsyncClient(base_url=_BASE_URL, timeout=10.0)

    async def get_arrivals(self, line_id: str) -> list[RawArrival]:
        try:
            response = await self._client.get(f"/Line/{line_id}/Arrivals/")
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise TflClientError(f"Failed to fetch arrivals for line '{line_id}'") from exc

        return [
            RawArrival(
                vehicle_id=item["vehicleId"],
                naptan_id=item["naptanId"],
                platform_name=item.get("platformName") or "",
                destination_name=item.get("destinationName") or item.get("towards") or "",
                time_to_station=item["timeToStation"],
                direction=item.get("direction") or "",
                current_location=item.get("currentLocation") or "",
            )
            for item in response.json()
        ]

    async def get_line_statuses(self, line_ids: list[str]) -> list[RawLineStatus]:
        today = datetime.date.today()
        tomorrow = today + datetime.timedelta(days=1)
        ids = ",".join(line_ids)
        try:
            response = await self._client.get(
                f"/Line/{ids}/Status/{today}/to/{tomorrow}",
                params={"detail": "true"},
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise TflClientError("Failed to fetch line statuses") from exc

        statuses = []
        for line in response.json():
            for status in line["lineStatuses"]:
                disruption = status.get("disruption") or {}
                affected_routes = [
                    RawRouteSection(
                        origin_name=route["originationName"],
                        destination_name=route["destinationName"],
                    )
                    for route in disruption.get("affectedRoutes", [])
                ]
                statuses.append(
                    RawLineStatus(
                        line_id=line["id"],
                        line_name=line["name"],
                        status_severity=status["statusSeverity"],
                        status_severity_description=status["statusSeverityDescription"],
                        reason=status.get("reason"),
                        affected_routes=affected_routes,
                    )
                )
        return statuses

    async def get_stop_point_disruptions(self) -> list[RawStopPointDisruption]:
        try:
            response = await self._client.get("/stopPoint/mode/tube/disruption")
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise TflClientError("Failed to fetch station disruptions") from exc

        return [
            RawStopPointDisruption(
                station_atco_code=item["atcoCode"],
                disruption_type=item["type"],
                description=item["description"],
            )
            for item in response.json()
        ]


@lru_cache
def get_tfl_client() -> TflClient:
    return TflClient()
