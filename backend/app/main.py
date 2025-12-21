from fastapi import FastAPI,status
from backend.app.api.main import api_router
from backend.app.core.config import settings
from contextlib import asynccontextmanager
from backend.app.core.db import init_db,engine, logger
from backend.app.core.logging import get_logger
from fastapi.responses import JSONResponse
from backend.app.core.health import health_checker,ServiceStatus
import asyncio
import time

logger = get_logger()

async def startup_health_check(timeout: float = 90.0) -> bool:
    start_time = time.time()
    while True:
        status = await health_checker.check_all_services()
        if all(s == ServiceStatus.HEALTHY for s in status.values()):
            logger.info("All services are healthy.")
            return True

        if time.time() - start_time > timeout:
            logger.error("Health check timed out.")
            return False

        await asyncio.sleep(2)

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await init_db()
        logger.info("Database initialized successfully.")
        await health_checker.add_service("database", health_checker.check_database)
        await health_checker.add_service("celery", health_checker.check_celery)
        await health_checker.add_service("redis", health_checker.check_redis)
        if not await startup_health_check():
            raise RuntimeError("Critical service failed tostart")
        logger.info("All Service initialize and healthy")
        yield
    except Exception as e:
        logger.error(f"Application startup failed: {e}")
        await engine.dispose()
        await health_checker.cleanup()
        raise
    finally:
        logger.info("Shutting down")
        await engine.dispose()
        await health_checker.cleanup()

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCTIPTION,
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

@app.get("/health", response_model=dict)
async def health_check():
    try:
        health_status = await health_checker.check_all_services()

        # Determine overall status
        if all(s == ServiceStatus.HEALTHY for s in health_status.values()):
            overall_status = ServiceStatus.HEALTHY
            status_code = status.HTTP_200_OK

        elif any(s == ServiceStatus.UNHEALTHY for s in health_status.values()):
            overall_status = ServiceStatus.UNHEALTHY
            status_code = status.HTTP_500_SERVICE_UNAVAILABLE

        else:
            overall_status = ServiceStatus.DEGRADED
            status_code = status.HTTP_206_PARTIAL_CONTENT

        return JSONResponse(
            status_code=status_code,
            content={
                "status": overall_status,
                "services": {k: v.value for k, v in health_status.items()},
            },
        )

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": ServiceStatus.UNHEALTHY,
                "error": str(e),
            },
        )


app.include_router(api_router, prefix=settings.API_V1_STR)