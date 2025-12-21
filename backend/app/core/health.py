import asyncio
import re
from typing import Dict, Any, Callable, Awaitable, Optional
from datetime import datetime, timedelta, timezone
from enum import Enum
from sqlalchemy import text
from backend.app.core.db import async_session
from backend.app.core.celery_app import celery_app
from backend.app.core.logging import get_logger

logger = get_logger()

class ServiceStatus(str, Enum):
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"
    STARTING = "starting"
    DOWN = "down"

class HealthCheck:
    def __init__(self):
        self._services: Dict[str, ServiceStatus] = {}
        self._check_functions: Dict[str, Callable[[], Awaitable[bool]]] = {}
        self._last_checked: Dict[str, datetime] = {}
        self._check_intervals: Dict[str, timedelta] = {} 
        self._timeouts: Dict[str, float] = {}
        self._retry_delays: Dict[str, float] = {}
        self._max_retries: Dict[str, int] = {}
        self._dependencies: Dict[str,set[str]] = {}
        self._cached_status: Optional[Dict[str, Any]] = None
        self._cache_duration: timedelta = timedelta(seconds=30)
        self._last_cache_time: Optional[datetime] = None

    async def validate_depencies(self, service_name: str, depends_on: list[str]) -> None:
        if not depends_on:
            return
        for dep in depends_on:
            if dep not in self._services:
                raise ValueError(
                    f"Dependency '{dep}' not registered for service '{service_name}'"
                )
            
    async def add_service(
            self,service_name: str, check_function: Callable[[], Awaitable[bool]], timeout: float=5.0, retry_delay: float=1.0, max_retries: int =3, depends_on: list[str] | None = None
    ) -> None:
        if service_name in self._services:
            raise ValueError(f"Service '{service_name}' is already registered.")
        if depends_on is None:
            depends_on = []
        await self.validate_depencies(service_name, depends_on)
        self._services[service_name] = ServiceStatus.STARTING
        self._check_functions[service_name] = check_function
        self._last_checked[service_name] = datetime.min.replace(tzinfo=timezone.utc)
        self._check_intervals[service_name] = timedelta(seconds=30)
        self._timeouts[service_name] = timeout
        self._retry_delays[service_name] = retry_delay
        self._max_retries[service_name] = max_retries
        self._dependencies[service_name] = set(depends_on)

    async def check_database(self) -> bool:
        try:
            async with async_session() as session:
                result = await session.execute(text("SELECT 1"))
                return result.scalar() == 1
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
        
    async def check_redis(self) -> bool:
        try:
            redis_client = celery_app.backend.client
            pong = redis_client.ping()
            self._last_checked['redis'] = datetime.now(timezone.utc)
            return pong is True
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return False
    async def check_celery(self) -> bool: 
        try:
            inspector = celery_app.control.inspect()
            worker = inspector.ping()

            if not worker:
                conn = celery_app.connection()
                try:
                    conn.ensure_connection(max_retries=3)
                    logger.warning("No Celery workers found, but connection to rabbitmq is successful.")
                    self._last_checked['celery'] = datetime.now(timezone.utc)
                    return True
                finally:
                    conn.close() 
            self._last_checked['celery'] = datetime.now(timezone.utc)
            return True
        except Exception as e:
            logger.error(f"Celery health check failed: {e}")
            return False
    async def checks_service_health(self, service_name:str, max_retries:int=5)-> ServiceStatus:
        if service_name not in self._services:
            raise ValueError(f"Service '{service_name}' is not registered.")
        check_function = self._check_functions[service_name]
        timeout = self._timeouts[service_name]
        retry_delay = self._retry_delays[service_name]
        for attempt in range(max_retries):
            try:
                is_healthy = await asyncio.wait_for(check_function(), timeout=timeout)
                if is_healthy:
                    self._services[service_name] = ServiceStatus.HEALTHY
                    self._last_checked[service_name] = datetime.now(timezone.utc)
                    return ServiceStatus.HEALTHY
                else:
                    logger.warning(f"Health check for service '{service_name}' returned unhealthy.")
            except asyncio.TimeoutError:
                logger.error(f"Health check for service '{service_name}' timed out.")
            except Exception as e:
                logger.error(f"Health check for service '{service_name}' failed: {e}")
            await asyncio.sleep(retry_delay)
        self._services[service_name] = ServiceStatus.UNHEALTHY
        return ServiceStatus.UNHEALTHY
    
    async def check_all_services(self) -> Dict[str, ServiceStatus]:
        tasks = []
        for service_name in self._services.keys():
            tasks.append(self.checks_service_health(service_name, self._max_retries[service_name]))
        results = await asyncio.gather(*tasks)
        return {service_name: status for service_name, status in zip(self._services.keys(), results)}
    
    async def wait_for_service(
            self, service_name: str, desired_status: ServiceStatus = ServiceStatus.HEALTHY, check_interval: float = 5.0, timeout: float = 60.0
    ) -> bool:
        start_time = datetime.now(timezone.utc)
        while (datetime.now(timezone.utc) - start_time).total_seconds() < timeout:
            current_status = await self.checks_service_health(service_name)
            if current_status == desired_status:
                return True
            await asyncio.sleep(check_interval)
        return False
    
    async def cleanup(self) -> None:
        self._services.clear()
        self._check_functions.clear()
        self._last_checked.clear()
        self._check_intervals.clear()
        self._timeouts.clear()
        self._retry_delays.clear()
        self._max_retries.clear()
        self._dependencies.clear()
        self._cached_status = None
        self._last_cache_time = None

health_checker = HealthCheck()


