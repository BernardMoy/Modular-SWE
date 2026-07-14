from functools import lru_cache

from app.clients.tfl_client import RawLineStatus, RawRouteSection, TflClient, get_tfl_client
from app.data.station_repository import StationRepository, get_station_repository
from app.models.line_status import LineSeverityGroup, LineStatusSummary, RouteSection

_GOOD_SERVICE = "Good Service"
_STATION_SUFFIX = " Underground Station"


class LineStatusService:
    def __init__(self, tfl_client: TflClient, station_repository: StationRepository):
        self._tfl_client = tfl_client
        self._station_repository = station_repository

    async def get_line_status_summaries(self) -> list[LineStatusSummary]:
        line_ids = self._station_repository.list_line_ids()
        raw_statuses = await self._tfl_client.get_line_statuses(line_ids)

        summaries = []
        for line_id in line_ids:
            disrupted_statuses = [
                status
                for status in raw_statuses
                if status.line_id == line_id
                and status.status_severity_description != _GOOD_SERVICE
            ]
            if not disrupted_statuses:
                continue
            summaries.append(
                LineStatusSummary(
                    line_id=line_id,
                    line_name=disrupted_statuses[0].line_name,
                    severities=self._group_by_severity(disrupted_statuses),
                )
            )
        return summaries

    @staticmethod
    def _group_by_severity(statuses: list[RawLineStatus]) -> list[LineSeverityGroup]:
        statuses_by_severity: dict[str, list[RawLineStatus]] = {}
        for status in statuses:
            statuses_by_severity.setdefault(status.status_severity_description, []).append(status)

        groups = []
        for severity_description, members in statuses_by_severity.items():
            raw_sections = [route for member in members for route in member.affected_routes]
            reasons = list(dict.fromkeys(member.reason for member in members if member.reason))
            groups.append(
                LineSeverityGroup(
                    severity_description=severity_description,
                    route_sections=_merge_route_sections(raw_sections),
                    reasons=reasons,
                )
            )
        return groups


def _merge_route_sections(raw_sections: list[RawRouteSection]) -> list[RouteSection]:
    pairs = [(_strip_suffix(r.origin_name), _strip_suffix(r.destination_name)) for r in raw_sections]
    pair_set = set(pairs)
    seen: set[tuple[str, str]] = set()

    merged = []
    for start, end in dict.fromkeys(pairs):
        if (start, end) in seen:
            continue
        if (end, start) in pair_set:
            merged.append(RouteSection(start=start, end=end, bidirectional=True))
            seen.add((start, end))
            seen.add((end, start))
        else:
            merged.append(RouteSection(start=start, end=end, bidirectional=False))
            seen.add((start, end))
    return merged


def _strip_suffix(name: str) -> str:
    return name[: -len(_STATION_SUFFIX)] if name.endswith(_STATION_SUFFIX) else name


@lru_cache
def get_line_status_service() -> LineStatusService:
    return LineStatusService(get_tfl_client(), get_station_repository())
