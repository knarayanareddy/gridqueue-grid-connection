from fastapi import FastAPI

from app.config import settings

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
