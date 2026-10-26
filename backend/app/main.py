from typing import Annotated, Any, Literal

from fastapi import Depends, FastAPI
from pydantic import BaseModel, Field

from app.config import Settings, get_settings, settings
from app.pipeline import Services, answer_query, build_services, new_run_id

TITLE = "GridQueue — Energy Grid Interconnection Navigator & Flex Planner"

app = FastAPI(
    title=TITLE,
    description=(
        "Navigate electrical grid congestion in the Netherlands — direction-aware (feed-in vs consumption) "
        "answers grounded in official grid-operator documents, a deterministic citation gate, and ranked "
        "non-firm / flexibility options."
    ),
    version="0.1.0",
)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok", "environment": settings.environment}


@app.get("/v1/info")
def get_info() -> dict[str, object]:
    return {
        "project": TITLE,
        "track": "Best Apps and Agents (Eligible for Best Use of Tavily $3,000)",
        "models": {
            "ultra": settings.model_ultra,
            "super": settings.model_super,
            "nano": settings.model_nano,
        },
        "keys_configured": {
            "nebius": settings.has_nebius_key,
            "tavily": settings.has_tavily_key,
        },
    }


class AnswerRequest(BaseModel):
    postcode: str = Field(min_length=4, max_length=8, description="Dutch postcode, e.g. '5612' or '5612 AB'")
    power_kw: float = Field(gt=0, le=100_000, description="Requested capacity in kW")
    direction: Literal["feed_in", "consumption"]


class ServiceFactory:
    """Dependency that builds per-request external services. Overridden in tests."""

    def __call__(self, cfg: Annotated[Settings, Depends(get_settings)]) -> tuple[Services, str, Settings]:
        run_id = new_run_id()
        return build_services(cfg, run_id), run_id, cfg


service_factory = ServiceFactory()


@app.post("/v1/answer")
async def post_answer(
    body: AnswerRequest,
    deps: Annotated[tuple[Services, str, Settings], Depends(service_factory)],
) -> dict[str, Any]:
    """Direction-aware answer. Returns a QueryResponse (schemas/core-schemas.json#/$defs/QueryResponse)."""
    services, run_id, cfg = deps
    return await answer_query(
        postcode=body.postcode,
        power_kw=body.power_kw,
        direction=body.direction,
        services=services,
        run_id=run_id,
        runs_dir=cfg.runs_dir,
    )


def run() -> None:
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.environment == "development",
    )


if __name__ == "__main__":
    run()
