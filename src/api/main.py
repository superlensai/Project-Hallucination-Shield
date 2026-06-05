import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.config import settings
from src.core.db_gate import db_gate
from src.api.routes import router as internal_router
from src.api.admin import router as admin_router

logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))
logger = logging.getLogger("halwall")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage startup and shutdown lifecycle."""
    logger.info(f"Starting HalWall API (env={settings.ENVIRONMENT})")
    await db_gate.initialize()
    yield
    logger.info("Shutting down HalWall API")
    await db_gate.shutdown()


app = FastAPI(
    title="HalWall Trusted Package Database API",
    version="0.1.0",
    docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
    lifespan=lifespan,
)

# CORS
if settings.CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[o.strip() for o in settings.CORS_ORIGINS.split(",")],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(internal_router)
app.include_router(admin_router)


@app.get("/internal/health")
async def health_check():
    """Basic liveness probe."""
    return {"status": "ok", "service": "halwall-api", "environment": settings.ENVIRONMENT}


@app.get("/internal/health/db")
async def db_health_check():
    """Deep health check including database connectivity and pool stats."""
    db_status = await db_gate.health_check()
    status_code = 200 if db_status["status"] == "healthy" else 503
    from fastapi.responses import JSONResponse
    return JSONResponse(content=db_status, status_code=status_code)


@app.get("/")
async def root():
    return {"message": "Welcome to HalWall Trusted Package Database API"}
