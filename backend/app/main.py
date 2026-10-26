from fastapi import FastAPI
from app.config import settings

app = FastAPI(
    title="GridQueue — Energy Grid Interconnection Navigator & Flex Planner",
    description="Navigate electrical grid congestion in the Netherlands and NW Europe — live DSO register and non-binding indicative forecast ('codeerprognose') discovery via Tavily, deterministic citation gating, and autonomous non-firm flexibility planning.",
    version="0.1.0"
)

@app.get("/health")
def health_check():
    return {"status": "ok", "environment": settings.environment}

@app.get("/v1/info")
def get_info():
    return {
        "project": "GridQueue — Energy Grid Interconnection Navigator & Flex Planner",
        "track": "Best Apps and Agents (Eligible for Best Use of Tavily $3,000)",
        "models": {
            "ultra": settings.model_ultra,
            "super": settings.model_super,
            "nano": settings.model_nano
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
