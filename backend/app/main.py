import os
from urllib.parse import urlsplit

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.models.replay import ReplayResponse
from backend.app.models.scenario import ScenarioListResponse
from backend.app.services.replay_service import ReplayService
from backend.app.services.scenario_loader import (
    ScenarioDataError,
    ScenarioLoader,
    ScenarioNotFoundError,
    ScenarioUnavailableError,
)


DEFAULT_CORS_ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173"]


def _is_valid_origin(origin: str) -> bool:
    try:
        parsed = urlsplit(origin)
    except ValueError:
        return False
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc) and not parsed.path


def _cors_origins() -> list[str]:
    configured = os.getenv("CORS_ORIGINS", "http://localhost:5173")
    origins = [
        origin
        for item in configured.split(",")
        if (origin := item.strip()) and _is_valid_origin(origin)
    ]
    if not origins:
        return DEFAULT_CORS_ORIGINS.copy()
    if "http://127.0.0.1:5173" not in origins:
        origins.append("http://127.0.0.1:5173")
    return origins


app = FastAPI(title="MOMENT API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


loader = ScenarioLoader()
replay_service = ReplayService(loader=loader)


@app.exception_handler(ScenarioDataError)
async def scenario_data_error_handler(
    _request: Request, exc: ScenarioDataError
) -> JSONResponse:
    return JSONResponse(status_code=422, content={"detail": str(exc)})


@app.exception_handler(ScenarioUnavailableError)
async def scenario_unavailable_handler(
    _request: Request, exc: ScenarioUnavailableError
) -> JSONResponse:
    return JSONResponse(status_code=503, content={"detail": str(exc)})


@app.get("/api/health")
def health() -> dict[str, str | bool]:
    return {
        "status": "ok",
        "service": "moment-api",
        "model_ready": False,
        "gemini_available": bool(os.getenv("GEMINI_API_KEY")),
        "mock_fallback_available": True,
    }


@app.get("/api/scenarios", response_model=ScenarioListResponse)
def scenarios() -> ScenarioListResponse:
    return ScenarioListResponse(scenarios=loader.list_scenarios())


@app.get("/api/replay/{scenario_id}", response_model=ReplayResponse)
def replay(scenario_id: str) -> ReplayResponse:
    try:
        return replay_service.build_replay(scenario_id)
    except ScenarioNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Unknown scenario_id") from exc
