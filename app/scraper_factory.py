from app.google_search import GoogleSearch
from app.config import settings


def scraper_factory(keyword: str):
    return GoogleSearch(
        api_key=settings.GOOGLE_API_KEY,
        search_engine_id=settings.GOOGLE_SEARCH_ENGINE_ID,
        client_id=settings.CLIENT_ID,
        keywords=[keyword],
    )
