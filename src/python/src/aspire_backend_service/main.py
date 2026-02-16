import logging
import json

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from .routers.agents import router as agents_router
from .telemetry import configure_telemetry

logging.basicConfig(level=logging.INFO)
app = FastAPI()

tracer = configure_telemetry(app, service_name="weather-api")
logger = logging.getLogger(__name__)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Custom handler for validation errors to log detailed information"""
    # Log the raw body
    body = b""
    try:
        body = await request.body()
        logger.error(f"Validation error on {request.method} {request.url.path}")
        logger.error(f"Request body (raw bytes): {body}")
        logger.error(f"Request body (decoded): {body.decode('utf-8', errors='replace')}")
        logger.error(f"Content-Type header: {request.headers.get('content-type')}")
        logger.error(f"Validation errors: {exc.errors()}")
    except Exception as e:
        logger.error(f"Error reading request body: {e}")

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": exc.errors(),
            "body": body.decode("utf-8", errors="replace") if body else None,
        },
    )


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests"""
    logger.info(f"Incoming request: {request.method} {request.url.path}")
    logger.debug(f"Headers: {dict(request.headers)}")

    response = await call_next(request)

    logger.info(f"Response status: {response.status_code}")
    return response


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
