from pydantic_settings import BaseSettings
from pydantic import PostgresDsn


class Settings(BaseSettings):
    DEBUG: bool = True
    
    REDIS_URL: str = "redis://localhost:6379"
    POSTGRES_URL: PostgresDsn
    GOOGLE_API_KEY: str
    GOOGLE_SEARCH_ENGINE_ID: str
    CLIENT_ID: str = "job-scraper"
    REDIS_EXPIRATION: int = 14400
    SCRAPER_API_KEY  : str = "your_scraper_api_key"
    @property
    def REDIS_HOST(self):
        return self.REDIS_URL.split("//")[-1].split(":")[0]

    @property
    def REDIS_PORT(self):
        return int(self.REDIS_URL.split(":")[-1])

    class Config:
        env_file = ".env"


settings = Settings()
