import json
import os
from functools import lru_cache

import httpx
from pydantic import BaseModel

_REDIS_KEY = "delay-estimates"


class DelayEstimatesClientError(Exception):
    pass


class RawDelayEstimate(BaseModel):
    trackernet_code: str
    vehicle_id: str
    closest_station_id_to_arrival: str
    current_location: str
    time_to_station: int
    direction: str
    timestamp: int
    delayed_seconds: float


class DelayEstimatesClient:
    def __init__(self, client: httpx.AsyncClient | None = None):
        self._client = client or httpx.AsyncClient(timeout=10.0)

    async def get_delay_estimates(self) -> list[RawDelayEstimate]:
        rest_url = os.environ["UPSTASH_REDIS_REST_URL"]
        rest_token = os.environ["UPSTASH_REDIS_REST_TOKEN"]

        try:
            response = await self._client.get(
                f"{rest_url}/get/{_REDIS_KEY}",
                headers={"Authorization": f"Bearer {rest_token}"},
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise DelayEstimatesClientError("Failed to fetch delay estimates") from exc

        try:
            raw_value = response.json()["result"]
            if raw_value is None:
                return []
            records = json.loads(raw_value)["data"]
            return [
                RawDelayEstimate(
                    trackernet_code=record["trackernetCode"],
                    vehicle_id=record["vehicleId"],
                    closest_station_id_to_arrival=record["closestStationIdToArrival"],
                    current_location=record["currentLocation"],
                    time_to_station=record["timeToStation"],
                    direction=record["direction"],
                    timestamp=record["timestamp"],
                    delayed_seconds=record["delayedSeconds"],
                )
                for record in records
            ]
        except (KeyError, TypeError, ValueError) as exc:
            raise DelayEstimatesClientError("Failed to parse delay estimates payload") from exc


@lru_cache
def get_delay_estimates_client() -> DelayEstimatesClient:
    return DelayEstimatesClient()
