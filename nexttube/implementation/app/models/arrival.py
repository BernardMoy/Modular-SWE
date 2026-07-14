from pydantic import BaseModel

_DUE_THRESHOLD_SECONDS = 30


class ArrivalBoardEntry(BaseModel):
    index: int
    destination_name: str
    time_display: str
    platform: str


class ArrivalBoard(BaseModel):
    direction: str
    entries: list[ArrivalBoardEntry]


def format_time_display(seconds_to_station: int) -> str:
    if seconds_to_station < _DUE_THRESHOLD_SECONDS:
        return "Due"
    minutes = round(seconds_to_station / 60)
    return f"{minutes} min"
