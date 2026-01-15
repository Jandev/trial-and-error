from fastapi import FastAPI

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/health/startup")
async def startup():
    """Startup probe - checks if the application has started successfully"""
    return {"status": "ok"}


@app.get("/health/live")
async def liveness():
    """Liveness probe - checks if the application is still running"""
    return {"status": "ok"}


@app.get("/health/ready")
async def readiness():
    """Readiness probe - checks if app is ready to handle requests"""
    # Add custom logic to check dependencies (database, services, etc.)
    return {"status": "ok"}
