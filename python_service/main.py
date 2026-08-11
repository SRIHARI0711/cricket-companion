"""
analytics_service – FastAPI entry point.

Start with:
    uvicorn main:app --reload
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from database import create_pool, close_pool
from routes import router


# ---------------------------------------------------------------------------
# Lifespan: create / close the DB pool around the app's lifetime
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_pool()
    yield
    await close_pool()


# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Cricket Companion – Analytics Service",
    description=(
        "A FastAPI microservice that provides advanced cricket analytics by "
        "querying the `cricket_companion` MySQL database.\n\n"
        "## Endpoints\n"
        "| Method | Path | Description |\n"
        "|--------|------|-------------|\n"
        "| GET | `/player/{id}/stats` | Career batting & bowling stats for a player |\n"
        "| GET | `/team/{id}/winrate` | Win-rate and match record for a team |\n"
        "| GET | `/match/compare` | Head-to-head comparison between two teams |\n"
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS – allow the frontend dev server and any localhost origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(router)


# ---------------------------------------------------------------------------
# Health-check
# ---------------------------------------------------------------------------

@app.get("/health", tags=["Health"], summary="Service health check")
async def health():
    return {"status": "ok", "service": "analytics_service", "version": "1.0.0"}


# ---------------------------------------------------------------------------
# Entry point for direct execution  (python main.py)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
