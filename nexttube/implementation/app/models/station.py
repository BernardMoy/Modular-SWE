from pydantic import BaseModel

_NAME_EXCEPTIONS = {
    "Nine Elms": "NIE",
    "Battersea Power Station": "BPS",
}


class Line(BaseModel):
    id: str
    name: str
    color: str


class Station(BaseModel):
    id: str
    name: str
    code: str
    lines: list[Line]


def derive_code(station_id: str, station_name: str) -> str:
    if station_name in _NAME_EXCEPTIONS:
        return _NAME_EXCEPTIONS[station_name]
    return station_id[-3:].upper()
