# Job Scraper Microservice

This is a FastAPI-based microservice that scrapes job listings using Google Custom Search, validates them, and saves them to a PostgreSQL database.  
It supports scheduled scraping and integration with Redis for cache control.

## Features

- ✅ Google search-based job discovery
- ✅ Redis-based keyword caching
- ✅ PostgreSQL-backed job post storage
- ✅ Dockerized microservice
- ✅ API endpoint for triggering scraping

## Project Structure

- `main.py` - FastAPI app entry point
- `scraper_service.py` - Core scraping logic
- `google_search.py` - Google CSE integration
- `redis_service.py` - Redis client wrapper
- `models/` - SQLAlchemy models
- `schemas/` - Pydantic schemas
- `init_db.py` - Table creation on startup

## Usage

Start the service:
```bash
docker compose up --build
```

Trigger scrape:
```http
POST /scrape
```
