# schemas/job_post.py

from typing import List, Optional
from pydantic import BaseModel, HttpUrl
from datetime import datetime


class JobPostBase(BaseModel):
    title: str
    link: HttpUrl
    keywords: List[str]


class JobPostCreate(JobPostBase):
    snippet: Optional[str] = None
    source: Optional[str] = None
    posted_time: Optional[datetime] = None
    company: Optional[str] = None
    validated: bool


class JobPostOut(JobPostBase):
    id: int
    snippet: Optional[str]
    # source: Optional[str]
    posted_time: Optional[datetime]
    scraped_at: Optional[datetime]  # instead of created_at
    location: Optional[str] = None
    company: Optional[str] = None
    validated: bool

    requirements: Optional[str] = None
    description: Optional[str] = None
    responsibilities: Optional[str] = None
    validated_date: Optional[datetime] = None

    # class Config:
    #     orm_mode = True
    model_config = {"from_attributes": True}
