from fastapi import APIRouter
from backend.app.core.logging import get_logger

router = APIRouter()

logger = get_logger()

@router.get("/home")
def home():
    logger.info("Home endpoint accessed")
    logger.debug("Debugging home endpoint")
    logger.error("This is a sample error log from home endpoint")
    logger.warning("This is a sample warning log from home endpoint")
    logger.critical("This is a sample critical log from home endpoint")
    return {"message": "Welcome to the Home Page"}