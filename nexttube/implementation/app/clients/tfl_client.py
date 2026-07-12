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
            )
            for item in response.json()
        ]


@lru_cache
def get_tfl_client() -> TflClient:
    return TflClient()
