from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import arrivals, stations

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

    return app


app = create_app()
