import datetime
import pytz

from pydantic import ValidationError
from app.models.JobPost import JobPost
from app.scraper_factory import scraper_factory
from app.schemas.job_post_schema import JobPostCreate
from app.log_config import logger


class JobScraperService:
    def __init__(self, redis_service, db):
        self.redis = redis_service
        # self.google = google_search
        self.db = db

    def scrape(self, keywords):
        added_jobs = 0
        skipped_jobs = 0
        missing_data_jobs = 0
        failed_saves = 0  # New counter for failed saves

        for keyword in keywords:
            if self.redis.was_scraped_recently(keyword):
                logger.info(f"Keyword '{keyword}' was scraped recently. Skipping...")
                continue

            scraper = scraper_factory(keyword)
            results = scraper.search(keyword)

            for result in results:
                # Extract job details
                link = result.get("link")
                title = result.get("title")
                logger.info(f"Scraped job: {title} - {link}")

                # Increment missing_data_jobs if title or link is missing
                if not link or not title:
                    missing_data_jobs += 1
                    logger.warning(f"Job missing title or link: {result}")
                    continue

                # Check if the job already exists in the database
                if self.job_exists(link):
                    logger.info(f"Job already exists: {link}")
                    job_post = self.db.query(JobPost).filter(JobPost.link == link).first()
                    self.update_keywords(job_post, keyword)
                    skipped_jobs += 1
                    continue

                # Attempt to save the job post
                if self.save_job_post(result, keyword):
                    added_jobs += 1
                else:
                    failed_saves += 1  # Increment failed saves if saving fails

            self.redis.mark_as_scraped(keyword)

        # Return all counts to the user
        return {
            "added_jobs": added_jobs,
            "skipped_jobs": skipped_jobs,
            "missing_data_jobs": missing_data_jobs,
            "failed_saves": failed_saves,
        }

    def job_exists(self, url: str) -> bool:
        # Query the database for the job post by URL
        job_post = self.db.query(JobPost).filter(JobPost.link == url).first()
        return job_post is not None

    def update_keywords(self, job_post: JobPost, keyword: str) -> None:
        # Append the keyword to the job's keywords list if not already present
        if keyword not in job_post.keywords:
            logger.info(f"Adding keyword {keyword} to job keywords {job_post.keywords}")
            job_post.keywords.append(keyword)
            try:
                self.db.commit()
                logger.info(f"Keyword '{keyword}' appended to existing job: {job_post.link}")
            except Exception as e:
                logger.error(f"Failed to append keyword '{keyword}' to job: {e}")
                self.db.rollback()

    def save_job_post(self, result: dict, keyword: str) -> bool:
        # Validate and transform the input data
        validated_data = self.validate_job_post_data(result, keyword)
        if not validated_data:
            return False  # Skip saving if validation fails

        logger.info(f"Saving job post: {validated_data}")
        # Create the JobPost object using validated data
        job_post = JobPost(
            **validated_data,
            scraped_at=datetime.datetime.now(pytz.timezone("Israel")),
        )

        # Add and commit the job post to the database
        self.db.add(job_post)
        try:
            self.db.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to commit job post to the database: {e}")
            self.db.rollback()  # Roll back the transaction to maintain database integrity
            return False

    def validate_job_post_data(self, result: dict, keyword: str) -> dict | None:
        try:
            # Validate the job post data
            validated = JobPostCreate(
                title=result.get("title"),
                link=result.get("link"),
                snippet=result.get("snippet"),
                source="job_scraper_cloud_GoogleSearch",
                keywords=[keyword],  # Use a list containing only the current keyword
                validated=False,
            )
            validated_data = validated.model_dump()
            validated_data["link"] = str(validated.link)  # Convert HttpUrl to string
            return validated_data  # Use model_dump() to convert the Pydantic model to a dictionary
        except ValidationError as e:
            logger.error(f"Skipping invalid job: {e}")
            return None
