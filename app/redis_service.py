# app/services/redis_service.py
import redis
from app.config import settings


class RedisService:
    def __init__(self, host=None, port=None, db=0):
        self.client = redis.Redis(
            host=host or settings.REDIS_HOST,
            port=port or settings.REDIS_PORT,
            db=db,
            decode_responses=True,
        )

    def was_scraped_recently(self, keyword: str) -> bool:
        return self.client.exists(f"scraped:{keyword}") == 1

    def mark_as_scraped(self, keyword: str, ttl: int = settings.REDIS_EXPIRATION):
        self.client.setex(f"scraped:{keyword}", ttl, "1")

    def get_client(self):
        return self.client  # Optional, if you still want direct access
