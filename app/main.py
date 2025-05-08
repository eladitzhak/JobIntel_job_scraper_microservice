from fastapi import Query
from fastapi import FastAPI, Request,Header, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from fastapi import Depends
from sqlalchemy import text
from typing import Optional
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.google_search import GoogleSearch
from app.redis_service import RedisService
from app.scraper_service import JobScraperService
from app.config import settings
from app.log_config import logger
from app.init_db import init_db
from app.models.JobPost import JobPost


if settings.DEBUG:
    import debugpy
    debugpy.listen(("0.0.0.0", 5678))
    print("🪲 Waiting for debugger to attach...")
    debugpy.wait_for_client()

logger.info("Starting FastAPI app...")
logger.info("Starting FastAPI app...")
logger.info("Test log message")
import os
print(os.getcwd())
app = FastAPI()

API_KEY = settings.SCRAPER_API_KEY  # read from .env

@app.on_event("startup")
async def startup_event():
    logger.info("🔌 strtupup event! Connecting to database...")
     # Optionally test the connection
    try:
        print("🔌 Testing DB connection...")
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


@app.get("/was-scraped-recently")
async def was_scraped_recently(keywords: list[str] = Query(...)):
    logger.info(f"/was-scraped-recently called with: {keywords}")
    redis = RedisService()
    results = {}

    for keyword in keywords:
        results[keyword] = redis.was_scraped_recently(keyword)

    return results

@app.get("/scrape-from-user")
async def scrape_from_user(
    keywords: list[str] = Query(...),
    x_api_key: Optional[str] = Header(None),
     db: AsyncSession = Depends(get_db),  # ✅ use async db
):
    if x_api_key != settings.SCRAPER_API_KEY:
        
        logger.warning("Unauthorized access attempt to /scrape-from-user")
        raise HTTPException(status_code=401, detail="Unauthorized")

    logger.info(f"/scrape-from-user called with: {keywords}")
    redis = RedisService()
    # db: Session = next(get_db())
    db: AsyncSession = Depends(get_db)
    scraper = JobScraperService(redis, db)

    # Scrape jobs for given keywords (modifies DB and sets Redis)
    scraper.scrape(keywords)

    # Fetch the new jobs just scraped (assuming scraped jobs have those keywords)
    stmt = select(JobPost).where(JobPost.keywords.overlap(keywords)).order_by(JobPost.scraped_at.desc()).limit(20)
    result = await db.execute(stmt)
    jobs = [dict(row._mapping) for row in result.fetchall()]

    return {
        "message": "Scraping done, returning fresh jobs",
        "keywords": keywords,
        "jobs": jobs
    }