from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy import Boolean, Column, Integer, String, DateTime, Text
from datetime import datetime
from typing import Optional
from app.database import Base  # Use Base from declarative_base()


# Base = declarative_base()
# Define the JobPost model
# This model represents a job post scraped from a website.
class JobPost(Base):
    __tablename__ = "job_posts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    snippet = Column(String)
    link = Column(String, unique=True)
    posted_time = Column(DateTime)
    keywords = Column(ARRAY(String))  # Use ARRAY for PostgreSQL
    # Alternatively, if using JSON:
    # keywords = Column(JSON)
    scraped_at = Column(DateTime, default=datetime.utcnow)
    location: Optional[str] = Column(String, nullable=True)  # Made location optional
    source = Column(String, nullable=False)  # Source of the job post (e.g., "GoogleSearch")
    # New columns:
    is_user_reported = Column(Boolean, default=False)  # Keep for fast filtering
    company = Column(String, nullable=True)  # Optional company name
    validated = Column(Boolean, nullable=False, default=False)  # Mark if job was validated

    validated_date = Column(DateTime, nullable=True)  # Date when the job was validated
    # Add any additional fields as needed
    requirements = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    responsibilities = Column(Text, nullable=True)
