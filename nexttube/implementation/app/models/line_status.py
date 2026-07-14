from pydantic import BaseModel


class RouteSection(BaseModel):
    start: str
    end: str
    bidirectional: bool


class LineSeverityGroup(BaseModel):
    severity_description: str
    route_sections: list[RouteSection]
    reasons: list[str]


class LineStatusSummary(BaseModel):
    line_id: str
    line_name: str
    severities: list[LineSeverityGroup]
