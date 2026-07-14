import re

from pydantic import BaseModel

_DIRECTIONS = ["Northbound", "Eastbound", "Southbound", "Westbound"]
_PLATFORM_NUMBER_RE = re.compile(r"\d+")


class PlatformInfo(BaseModel):
    direction: str | None
    platform_number: str | None


def parse(platform_name: str) -> PlatformInfo:
    direction = next(
        (d for d in _DIRECTIONS if d.lower() in platform_name.lower()),
        None,
    )
    match = _PLATFORM_NUMBER_RE.search(platform_name)
    platform_number = match.group() if match else None
    return PlatformInfo(direction=direction, platform_number=platform_number)
