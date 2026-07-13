from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import arrivals, line_map, line_statuses, lines, station_disruptions, stations

_FRONTEND_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]


def create_app() -> FastAPI:
    app = FastAPI(title="NextTube API")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=_FRONTEND_ORIGINS,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(stations.router, prefix="/api/stations", tags=["stations"])
    app.include_router(arrivals.router, prefix="/api/arrivals", tags=["arrivals"])
    app.include_router(line_statuses.router, prefix="/api/line-statuses", tags=["line-statuses"])
    app.include_router(
        station_disruptions.router, prefix="/api/station-disruptions", tags=["station-disruptions"]
    )
    app.include_router(lines.router, prefix="/api/lines", tags=["lines"])
    app.include_router(line_map.router, prefix="/api/line-map", tags=["line-map"])

    return app


app = create_app()
