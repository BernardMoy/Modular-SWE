import re
from typing import Literal

from pydantic import BaseModel

LocationKind = Literal["at_station", "at_platform", "left_station", "between_stations", "unknown"]

_AT_PLATFORM_RE = re.compile(r"^at\s+platform$", re.IGNORECASE)
_AT_STATION_RE = re.compile(r"^at\s+(.+)$", re.IGNORECASE)
_PLATFORM_SUFFIX_RE = re.compile(r"\s+platform\s+\S+$", re.IGNORECASE)
_APPROACHING_RE = re.compile(r"^approaching\s+(.+)$", re.IGNORECASE)
_LEFT_STATION_RE = re.compile(r"^(?:left|leaving|departed|departing)\s+(.+)$", re.IGNORECASE)
_BETWEEN_RE = re.compile(r"^between\s+(.+?)\s+and\s+(.+)$", re.IGNORECASE)


class ParsedLocation(BaseModel):
    kind: LocationKind
    station_name: str | None = None
    second_station_name: str | None = None


def parse(raw_location: str) -> ParsedLocation:
    text = raw_location.strip()

    if _AT_PLATFORM_RE.match(text):
        return ParsedLocation(kind="at_platform")

    match = _AT_STATION_RE.match(text)
    if match:
        station = _PLATFORM_SUFFIX_RE.sub("", match.group(1)).strip()
        return ParsedLocation(kind="at_station", station_name=station)

    match = _APPROACHING_RE.match(text)
    if match:
        return ParsedLocation(kind="at_station", station_name=match.group(1).strip())

    match = _LEFT_STATION_RE.match(text)
    if match:
        return ParsedLocation(kind="left_station", station_name=match.group(1).strip())

    match = _BETWEEN_RE.match(text)
    if match:
        return ParsedLocation(
            kind="between_stations",
            station_name=match.group(1).strip(),
            second_station_name=match.group(2).strip(),
        )

    return ParsedLocation(kind="unknown")
