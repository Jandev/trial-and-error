import logging

from fastapi import FastAPI

from .routers.agents import router as agents_router
from .telemetry import configure_telemetry

logging.basicConfig(level=logging.INFO)
app = FastAPI()

tracer = configure_telemetry(app, service_name="weather-api")
logger = logging.getLogger(__name__)


app.include_router(agents_router)


@app.get("/")
async def root():
    logger.info("Root endpoint called")
    return {"message": "Hello World"}


@app.get("/health/startup")
async def startup():
    """Startup probe - checks if the application has started successfully"""
    logger.info("Startup check called")
    return {"status": "ok"}


@app.get("/health/live")
async def liveness():
    """Liveness probe - checks if the application is still running"""
    logger.info("Live check called")
    return {"status": "ok"}


@app.get("/health/ready")
async def readiness():
    """Readiness probe - checks if app is ready to handle requests"""
    # Add custom logic to check dependencies (database, services, etc.)
    logger.info("Ready check called")
    return {"status": "ok"}
