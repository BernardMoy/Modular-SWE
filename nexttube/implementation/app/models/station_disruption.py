from pydantic import BaseModel


class StationDisruption(BaseModel):
    type: str
    description: str
