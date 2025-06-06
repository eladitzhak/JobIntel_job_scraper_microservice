from fastapi import FastAPI, Request,Header, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from fastapi import Depends
from sqlalchemy import text
from app.database import get_db
from app.google_search import GoogleSearch
from app.redis_service import RedisService
from app.scraper_service import JobScraperService
from app.config import settings
from app.log_config import logger
from app.init_db import init_db
from typing import Optional

if settings.DEBUG:
    import debugpy
    debugpy.listen(("0.0.0.0", 5678))
    print("🪲 Waiting for debugger to attach...")
    debugpy.wait_for_client()

logger.info("Starting FastAPI app...")
logger.info("Starting FastAPI app...")
logger.info("Test log message")
app = FastAPI()

API_KEY = settings.SCRAPER_API_KEY  # read from .env

@app.on_event("startup")
async def startup_event():
    logger.info("🔌 strtupup event! Connecting to database...")
     # Optionally test the connection
    try:
        logger.info("🔌 Testing DB connection...")
        init_db()  # Ensure the database is initialized
        logger.info("🔌 Database connection successful!")
    except Exception as e:
        logger.error("❌ Failed to connect to DB:", e)
    
@app.get("/health")
async def health_check():
    logger.info("/health route called!")
    return {"status": "ok"}


@app.get("/")
async def root():
    return {"message": "Welcome to the Job Scraper API!"}


class ScrapeRequest(BaseModel):
    keywords: list[str]


@app.post("/scrape")
async def scrape_jobs(
    payload: ScrapeRequest,
    x_api_key: Optional[str] = Header(None),  # 👈 optional
):
    if x_api_key != settings.SCRAPER_API_KEY:
        logger.warning("Unauthorized access attempt to /scrape")
        raise HTTPException(status_code=401, detail="Unauthorized")
    logger.info("/scrape route authorized")
    logger.info("/scrape route called!")
    logger.info(f"Received scrape request with keywords: {payload.keywords}")
    redis = RedisService()
    db: Session = next(get_db())
    scraper = JobScraperService(redis, db)
    
    # Call the scrape method and get the result
    scrape_result = scraper.scrape(payload.keywords)
    
    # Return the result to the user
    return {
        "message": "Scraping completed.",
        "keywords": payload.keywords,
        "results": scrape_result,  # Include the detailed counts
    }


@app.get("/health/db")
async def check_db_connection(db: Session = Depends(get_db)):
    logger.info("/health/db route called!")
    logger.info("Checking database connection...")
    try:
        result = db.execute(text("SELECT 1"))
        return {"db": "connected"}
        result = db.execute(text("SELECT * from JOB_POSTS limit 1"))

        rows = result.fetchall()
        # Convert to list of dicts
        rows_as_dicts = [dict(row._mapping) for row in rows]
        logger.info(f"Database connection successful! Rows: {rows_as_dicts}")
        return {"db": "connected", "result": rows_as_dicts}

    except Exception as e:
        logger.error(f"Database connection failed: {str(e)}")
        return {"db": "error", "details": str(e)}
