# app/services/google_scraper.py
###new
import random
import time
from datetime import datetime  # Import datetime for timestamp
from urllib.parse import quote_plus
import requests

from app.log_config import logger



class GoogleSearch:
    """
    A class to interact with the Google Custom Search API for job postings.
    """

    _BASE_URL = "https://www.googleapis.com/customsearch/v1"
    _DEFAULT_LOCATION = (
        """"Israel" OR "Tel Aviv" OR "Haifa" OR "Jerusalem" OR "Herzliya" OR "Ramat Gan" """
    )
    #     OR "Petah Tikva" OR """
    #     """"Rehovot" OR "Netanya" OR "Ra'anana" OR "Rishon Lezion" OR "Hod Hasharon" OR "Kfar Saba" OR """
    #     """"Beer Sheva" OR "Modiin" OR "Holon" OR "Bat Yam" OR "Ashdod" OR "Ashkelon" OR "Eilat" OR """
    #     """"Nazareth" OR "Tiberias" OR "Safed" OR "Afula" OR "Hadera" OR "Kiryat Gat" OR """
    #     """"Kiryat Yam" OR "Kiryat Bialik" OR "Kiryat Motzkin" OR "Kiryat Ata" OR "Kiryat Tivon" OR """
    #     """"Kiryat Malachi" OR "Kiryat Shmona" """
    # )
    # _DEFAULT_LOCATION = (
    #     "Tel Aviv", "Haifa", "Jerusalem", "Herzliya", "Ramat Gan")
    _DEFAULT_NUM_RESULTS = 20
    _DATE_RESTRICT = "d2"  # Restrict results to the last week
    _ALLOWED_JOB_SITES = (
        "boards.greenhouse.io",
        "jobs.lever.co",
        "comeet.com",
        "workday.com",
    )

    def __init__(
        self,
        api_key: str,
        search_engine_id: str,
        client_id: str,
        keywords: list[str],
        location: str = _DEFAULT_LOCATION,
        num_results: int = _DEFAULT_NUM_RESULTS,
        redis_client=None,  # Optional Redis client for caching
        db=None,  # Optional database session for storing results
    ) -> None:
        """
        Initialize the GoogleSearch instance with API credentials, keywords, location,
        and the desired number of results per search.

        Args:
            api_key (str): Google API key.
            search_engine_id (str): Google Search Engine ID.
            client_id (str): Google Client ID.
            keywords (List[str]): List of job-related keywords.
            location (str): Job location. Defaults to "ISRAEL".
            num_results (int): Number of search results to retrieve. Defaults to 20.
        """
        if not keywords:
            raise ValueError("Keywords list cannot be empty.")
        if not isinstance(keywords, list):
            raise ValueError("Keywords must be a list of strings.")
        if not isinstance(location, str):
            raise ValueError("Location must be a string.")
        if not isinstance(num_results, int) or num_results <= 0:
            raise ValueError("Number of results must be a positive integer.")

        self.api_key = api_key
        self.search_engine_id = search_engine_id
        self.client_id = client_id
        self.keywords = keywords
        if location:
            self.location = location
        else:
            self.location = self._DEFAULT_LOCATION
        self.num_results = num_results
        # self.results = []
        if not all([self.client_id, self.api_key, self.search_engine_id]):
            raise ValueError("Google API credentials are not set in environment variables.")
        if not isinstance(location, str):
            raise ValueError("Location must be a string.")
        if not isinstance(num_results, int) or num_results <= 0:
            raise ValueError("Number of results must be a positive integer.")
        self.results = []

    def build_query(self) -> str:
        """
        Construct the search query string.

        Returns:
            str: The constructed search query.
        """
        keywords_clause = " OR ".join([f'"{kw}"' for kw in self.keywords])
        sites_query = " OR ".join([f"site:{site}" for site in self._ALLOWED_JOB_SITES])
        return (
            f"{sites_query} ({keywords_clause}) "  # TODO: what to do with senior? by user?  # noqa: E501
            f"({self.location})"
        )

    def is_snippet_valid_for_israel(self, snippet: str) -> bool:
        """
        Check if the snippet indicates a job located in Israel.

        Args:
            snippet (str): The snippet text from the search result.

        Returns:
            bool: True if the job is located in Israel, False otherwise.
        """
        return "Israel, Italy" not in snippet.title()

    def search(self, keywords: list[str] = None) -> list[dict[str, str]]:
        """
        Perform the Google Custom Search and retrieve job postings.

        Returns:
            List[Dict[str, Optional[str]]]: A list of job postings with relevant details.
        """
        start_index = 1  # Start from the first result
        while len(self.results) < self.num_results:
            params = self.build_params(start_index)
            response = requests.get(self._BASE_URL, params=params)
            data = response.json()
            if "items" not in data:
                if start_index == 1:
                    logger.info("No results found for the initial search.")
                break  # Stop if there are no more results
            self.results.extend(self.parse_results(data))
            start_index += 10
            # Introduce a random delay between requests to avoid hitting the API too quickly
            time.sleep(random.uniform(1, 3))  # Random delay between 1 and 3 seconds
        return self.results

    def build_url(self, keywords_clause: str, location_part: str) -> str:
        query = self.build_query(keywords_clause, location_part)
        encoded = quote_plus(query)
        return f"https://www.google.com/search?q={encoded}&tbs=qdr:w2"

    def parse_results(self, data: dict) -> list[dict[str, str]]:
        results = []
        for item in data.get("items", []):
            # Check if the item is from Israel location
            if not self.is_snippet_valid_for_israel(item.get("snippet", "")):
                continue
            results.append(
                {
                    "title": item.get("title"),
                    "link": item.get("link"),
                    "snippet": item.get("snippet"),
                    "formattedUrl": item.get("formattedUrl"),
                    "displayLink": item.get("displayLink"),
                    "htmlFormattedUrl": item.get("htmlFormattedUrl"),
                    "htmlSnippet": item.get("htmlSnippet"),
                    "pagemap": item.get("pagemap"),
                    "searchInformation": item.get("searchInformation"),
                    "kind": item.get("kind"),
                    "cacheId": item.get("cacheId"),
                    "contextLink": item.get("contextLink"),
                }
            )
        return results

    def build_params(self, start_index: int) -> dict:
        return {
            "key": self.api_key,  # attribue and not property
            "cx": self.search_engine_id,
            "q": self.build_query(),
            "num": min(
                10, self.num_results - len(self.results)
            ),  # Fetch up to 10 results per request  # noqa: E501
            "start": start_index,
            "sort": "date",  # Sort results by recency
            # "dateRestrict": self._DATE_RESTRICT,      # Only results from the last 1 week
        }
